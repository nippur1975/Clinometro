# license_generator.py
# Este script genera claves de licencia para clinometro.py

import hashlib
import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("Advertencia: Biblioteca 'pyperclip' no encontrada. La funcionalidad de copiar al portapapeles no estará disponible automáticamente.")

# --- Constantes para la Licencia ---
# ¡¡ESTA CLAVE DEBE SER IDÉNTICA A LA USADA EN clinometro.py!!
SECRET_KEY = "my_super_secret_clinometer_key" 

# --- Funciones de Licencia (adaptadas de clinometro.py) ---
def generate_license_key(user_identifier: str) -> str:
    """
    Genera una clave de licencia basada en el identificador del usuario y la clave secreta.
    """
    m = hashlib.sha256()
    m.update(user_identifier.encode('utf-8'))
    m.update(SECRET_KEY.encode('utf-8'))
    return m.hexdigest()[:32] # Tomar los primeros 32 caracteres, igual que en clinometro

def store_license_data_here(license_key: str, internal_machine_id: str, directory: str) -> bool:
    """
    Guarda la clave de licencia y el ID de máquina en un archivo license.json 
    en el directorio especificado.
    """
    data = {
        "license_key": license_key,
        "machine_identifier": internal_machine_id 
    }
    filepath = os.path.join(directory, "license.json")
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error al guardar la licencia en {filepath}: {e}")
        return False

# --- Interfaz Gráfica (Tkinter) ---
class LicenseGeneratorApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Generador de Licencias - Clinómetro")
        self.root.geometry("500x300") # Tamaño de la ventana

        self.machine_id_var = tk.StringVar()
        self.generated_key_var = tk.StringVar()

        # Sección de entrada para ID de Máquina
        tk.Label(self.root, text="ID de Máquina (de clinometro.py):").pack(pady=(10,0))
        self.machine_id_entry = tk.Entry(self.root, textvariable=self.machine_id_var, width=50)
        self.machine_id_entry.pack(pady=5)

        # Botón para generar clave
        self.generate_button = tk.Button(self.root, text="Generar Clave de Licencia", command=self.generate_and_display_key)
        self.generate_button.pack(pady=10)

        # Sección para mostrar clave generada
        tk.Label(self.root, text="Clave de Licencia Generada:").pack(pady=(10,0))
        self.generated_key_entry = tk.Entry(self.root, textvariable=self.generated_key_var, width=50, state='readonly')
        self.generated_key_entry.pack(pady=5)

        # Botones de acción
        self.action_frame = tk.Frame(self.root)
        self.action_frame.pack(pady=10)

        self.copy_button = tk.Button(self.action_frame, text="Copiar Clave", command=self.copy_key_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.action_frame, text="Guardar license.json", command=self.save_license_file, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Mensaje sobre pyperclip
        if not PYPERCLIP_AVAILABLE:
            tk.Label(self.root, text="Pyperclip no encontrado. Copiar no disponible.", fg="red").pack(pady=(5,0))


    def generate_and_display_key(self):
        machine_id = self.machine_id_var.get().strip()
        if not machine_id:
            messagebox.showerror("Error", "El ID de Máquina no puede estar vacío.")
            return

        license_key = generate_license_key(machine_id)
        self.generated_key_var.set(license_key)

        self.copy_button.config(state=tk.NORMAL if PYPERCLIP_AVAILABLE else tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)

    def copy_key_to_clipboard(self):
        license_key = self.generated_key_var.get()
        if license_key and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(license_key)
                messagebox.showinfo("Copiado", "Clave de licencia copiada al portapapeles.")
            except Exception as e:
                messagebox.showerror("Error al Copiar", f"No se pudo copiar al portapapeles: {e}")
        elif not PYPERCLIP_AVAILABLE:
            messagebox.showwarning("Advertencia", "La biblioteca 'pyperclip' no está instalada. No se puede copiar automáticamente.")

    def save_license_file(self):
        machine_id = self.machine_id_var.get().strip()
        license_key = self.generated_key_var.get()

        if not machine_id or not license_key:
            messagebox.showerror("Error", "Se necesita un ID de máquina y una clave generada para guardar.")
            return

        # Guardar en el directorio actual del script generador
        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        
        if store_license_data_here(license_key, machine_id, current_script_directory):
            messagebox.showinfo("Guardado", f"Archivo 'license.json' guardado exitosamente en:\n{current_script_directory}")
        else:
            messagebox.showerror("Error al Guardar", "No se pudo guardar el archivo 'license.json'. Verifique la consola para más detalles.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LicenseGeneratorApp(root)
    root.mainloop()
