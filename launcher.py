import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import time
import urllib.request
import urllib.error

# CONFIGURACIÓN
SERVER_SCRIPT = "server.py"
HEALTH_URL = "http://127.0.0.1:8010/health"
process = None

def get_python_path():
    # Busca el python del entorno virtual
    venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

def check_server_ready():
    """
    Esta función se ejecuta en bucle cada 1 segundo.
    Intenta conectar con el servidor. Si falla, sigue intentando.
    Si conecta, activa el botón de Word.
    """
    global process
    if process is None: 
        return # Se detuvo manualmente

    try:
        # Intentamos hacer un GET al endpoint de salud con timeout corto
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
            if response.getcode() == 200:
                # cargado correctamente
                set_ui_state("READY")
                return
    except (urllib.error.URLError, ConnectionRefusedError):
        # El servidor aún está cargando el modelo o descargándolo.
        # No hacemos nada, espera al siguiente ciclo.
        pass
    except Exception as e:
        print(f"Error polling: {e}")

    # Si llegamos aquí, es que aún no está listo. Reintentar en 1000ms (1s)
    lbl_status.config(text=f"Estado: CARGANDO MODELO IA... ({int(time.time()) % 60}s)")
    root.after(1000, check_server_ready)

def start_server():
    global process
    if process is not None:
        return
    
    python_exe = get_python_path()
    
    try:
        # Configurar estado visual de "Cargando"
        set_ui_state("LOADING")
        
        # Iniciar el proceso del servidor oculto
        process = subprocess.Popen(
            [python_exe, SERVER_SCRIPT],
            cwd=os.getcwd()
        )
        
        # Iniciar el bucle de verificación
        # Esperamos 2 segundos iniciales para darle aire al proceso
        root.after(2000, check_server_ready)
        
    except Exception as e:
        messagebox.showerror("Error Crítico", f"No se pudo iniciar Python:\n{e}")
        stop_server()

def stop_server():
    global process
    if process:
        process.terminate()
        process = None
    set_ui_state("STOPPED")

def open_word():
    try:
        subprocess.Popen("start winword", shell=True)
    except:
        messagebox.showinfo("Info", "Abre Microsoft Word manualmente.")

def on_closing():
    stop_server()
    root.destroy()

# GESTIÓN DE LA INTERFAZ
def set_ui_state(state):
    if state == "STOPPED":
        lbl_status.config(text="Estado: DETENIDO", foreground="red")
        btn_start.config(state="normal", text=":) Iniciar Agente")
        btn_stop.config(state="disabled")
        btn_open_word.config(state="disabled") 
        
    elif state == "LOADING":
        lbl_status.config(text="Estado: INICIANDO MOTOR... (Espere)", foreground="#e67e22") 
        btn_start.config(state="disabled", text="Cargando...")
        btn_stop.config(state="normal")
        btn_open_word.config(state="disabled") 
        
    elif state == "READY":
        lbl_status.config(text="Estado: :) LISTO", foreground="green")
        btn_start.config(text="Agente Activo")
        btn_stop.config(state="normal")
        btn_open_word.config(state="normal") 

# GUI
root = tk.Tk()
root.title("Agente word AI")
root.geometry("400x280")
root.resizable(False, False)

# Estilos
style = ttk.Style()
style.theme_use('clam')

frame = ttk.Frame(root, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Panel de Control del Agente", font=("Segoe UI", 14, "bold")).pack(pady=10)

lbl_status = ttk.Label(frame, text="Estado: DETENIDO...", foreground="red", font=("Segoe UI", 10))
lbl_status.pack(pady=10)

btn_start = ttk.Button(frame, text=":) Iniciar Agente", command=start_server)
btn_start.pack(fill=tk.X, pady=5)

btn_stop = ttk.Button(frame, text=":/ Detener Agente", command=stop_server, state="disabled")
btn_stop.pack(fill=tk.X, pady=5)

ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=15)

# Este botón empieza DESHABILITADO hasta que el server responda
btn_open_word = ttk.Button(frame, text="Abrir Word", command=open_word, state="disabled")
btn_open_word.pack(fill=tk.X, pady=5)

ttk.Label(frame, text="Si es la primera vez, la carga puede tardar minutos.", font=("Segoe UI", 8), foreground="gray").pack(side=tk.BOTTOM)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()