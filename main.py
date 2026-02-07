import os, sys, shutil, subprocess
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Логика определения пути для работы внутри .exe
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS # Путь внутри временной папки .exe
else:
    base_path = os.path.dirname(__file__) # Путь в обычной папке

TEXCONV_PATH = os.path.join(base_path, "texconv.exe")
TEMP_DIR = "temp_textures"
DDS_FORMAT = "DXT5" # Стандарт для большинства скинов WT

def process_image(file_path, output_path, scale_factor, skip_if_small):
    base_name = os.path.basename(file_path)
    name_no_ext = os.path.splitext(base_name)[0]
    temp_png_path = os.path.join(TEMP_DIR, name_no_ext + ".png")

    try:
        with Image.open(file_path) as img:
            w, h = img.size
            
            # Пропуск, если файл уже 4K или меньше
            if skip_if_small and scale_factor < 1.0 and max(w, h) <= 4096:
                shutil.copy2(file_path, output_path)
                return f"[SKIP] {base_name}: уже {w}x{h}. Скопирован."

            # Ресайз
            new_w, new_h = int(w * scale_factor), int(h * scale_factor)
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
            resized.save(temp_png_path, "PNG")
            
            # Конвертация с принудительным использованием формата DX9 для GIMP
            output_dir = os.path.dirname(output_path)
            subprocess.run([
                TEXCONV_PATH, 
                "-ft", "DDS", 
                "-f", "DXT5", 
                "-dx9",       # Добавляем этот флаг для совместимости
                "-y", 
                "-o", output_dir, 
                temp_png_path
            ], check=True, capture_output=True)
            
            if os.path.exists(temp_png_path): os.remove(temp_png_path)
            return f"[OK] {base_name}: {w}x{h} -> {new_w}x{new_h}"
    except Exception as e:
        return f"[ERR] {base_name}: {str(e)}"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WT Skin Optimizer")
        self.geometry("700x500")
        
        # UI элементы (упрощенно)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Путь к скину:").grid(row=0, column=0, pady=(10,0))
        self.input_entry = ctk.CTkEntry(self, width=500)
        self.input_entry.grid(row=1, column=0, padx=20, pady=5)
        ctk.CTkButton(self, text="Выбрать папку", command=self.select_folder).grid(row=2, column=0, pady=5)

        self.scale_var = ctk.StringVar(value="0.5")
        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.grid(row=3, column=0, pady=10, padx=20, sticky="ew")
        ctk.CTkRadioButton(self.opt_frame, text="Сжать 2x", variable=self.scale_var, value="0.5").pack(side="left", padx=10)
        ctk.CTkRadioButton(self.opt_frame, text="Сжать 4x", variable=self.scale_var, value="0.25").pack(side="left", padx=10)
        ctk.CTkRadioButton(self.opt_frame, text="Растянуть 2x", variable=self.scale_var, value="2.0").pack(side="left", padx=10)

        self.skip_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Не трогать файлы 4K и меньше", variable=self.skip_var).grid(row=4, column=0, pady=5)

        ctk.CTkButton(self, text="ПУСК", fg_color="green", command=self.start).grid(row=5, column=0, pady=20)
        
        self.log_box = ctk.CTkTextbox(self, height=150)
        self.log_box.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, path)

    def start(self):
        folder = self.input_entry.get()
        if not folder: return
        
        out_folder = os.path.join(os.path.expanduser("~"), "Downloads", os.path.basename(folder) + "_DSCL")
        if not os.path.exists(out_folder): os.makedirs(out_folder)

        for f in os.listdir(folder):
            full_path = os.path.join(folder, f)
            if f.lower().endswith(".dds"):
                res = process_image(full_path, os.path.join(out_folder, f), float(self.scale_var.get()), self.skip_var.get())
                self.log_box.insert("end", res + "\n")
            elif os.path.isfile(full_path):
                shutil.copy2(full_path, os.path.join(out_folder, f))
        
        if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        messagebox.showinfo("Готово", f"Сохранено в: {out_folder}")

if __name__ == "__main__":
    App().mainloop()