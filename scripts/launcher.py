import sys
import os
import subprocess
import time
import traceback
import ctypes

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
    BASE_DIR = os.path.dirname(SCRIPT_DIR)
    
    SERVER_SCRIPT = os.path.join(BASE_DIR, "backend", "server.py")
    ICON_PATH = os.path.join(BASE_DIR, "frontend", "static", "icon.ico")
    
    VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
    if not os.path.exists(VENV_PYTHON):
        VENV_PYTHON = sys.executable

    sys.path.append(BASE_DIR)

except Exception as e:
    ctypes.windll.user32.MessageBoxW(0, f"Error iniciando rutas:\n{e}", "Error Fatal Titi", 0x10)
    sys.exit(1)

import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEALTH_URL = "https://127.0.0.1:8010/health"
process = None

def check_server_ready():
    global process
    if process is None: return 

    if process.poll() is not None:
        set_ui_state("STOPPED")
        return

    try:
        with urllib.request.urlopen(HEALTH_URL, context=ctx, timeout=1) as response:
            if response.getcode() == 200:
                set_ui_state("READY")
                return
    except:
        pass 

    lbl_status.config(text=f"Estado: CARGANDO MODELO... ({int(time.time()) % 60}s)")
    root.after(1000, check_server_ready)

def start_server():
    global process
    if process is not None: return
    
    if not os.path.exists(SERVER_SCRIPT):
        messagebox.showerror("Error", f"Falta server.py en:\n{SERVER_SCRIPT}")
        return

    try:
        set_ui_state("LOADING")
        
        creation_flags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        
        process = subprocess.Popen(
            [VENV_PYTHON, SERVER_SCRIPT],
            cwd=BASE_DIR, 
            creationflags=creation_flags
        )
        
        root.after(2000, check_server_ready)
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar:\n{e}")
        stop_server()

def stop_server():
    global process
    if process:
        try:
            process.terminate()
        except: pass
        process = None
    set_ui_state("STOPPED")

def open_word():
    try:
        subprocess.Popen("start winword", shell=True)
    except:
        messagebox.showinfo("Info", "Abre Word manualmente.")

def on_closing():
    stop_server()
    root.destroy()

def set_ui_state(state):
    if state == "STOPPED":
        lbl_status.config(text="Estado: DETENIDO", foreground="red")
        btn_start.config(state="normal", text="▶ Iniciar Agente")
        btn_stop.config(state="disabled")
        btn_open_word.config(state="disabled")
    elif state == "LOADING":
        lbl_status.config(text="Estado: INICIANDO MOTOR...", foreground="#e67e22")
        btn_start.config(state="disabled", text="Cargando...")
        btn_stop.config(state="normal")
    elif state == "READY":
        lbl_status.config(text="Estado: ● ONLINE (Listo)", foreground="green")
        btn_start.config(text="Agente Activo")
        btn_stop.config(state="normal")
        btn_open_word.config(state="normal")

try:
    root = tk.Tk()
    root.title("Titi AI Local")
    root.geometry("380x250")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width/2) - (380/2)
    y = (screen_height/2) - (250/2)
    root.geometry('%dx%d+%d+%d' % (380, 250, x, y))

    style = ttk.Style()
    style.theme_use('clam')
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Titi AI Manager", font=("Arial", 14, "bold")).pack(pady=5)
    lbl_status = ttk.Label(main_frame, text="Estado: DETENIDO", foreground="red")
    lbl_status.pack(pady=10)
    
    btn_start = ttk.Button(main_frame, text="▶ Iniciar Agente", command=start_server)
    btn_start.pack(fill=tk.X, pady=5)
    
    btn_stop = ttk.Button(main_frame, text="⏹ Detener", command=stop_server, state="disabled")
    btn_stop.pack(fill=tk.X, pady=5)
    
    ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
    
    btn_open_word = ttk.Button(main_frame, text="Abrir Word", command=open_word, state="disabled")
    btn_open_word.pack(fill=tk.X)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

except Exception as e:
    with open(os.path.join(SCRIPT_DIR, "launcher_error.txt"), "w") as f:
        f.write(traceback.format_exc())
    ctypes.windll.user32.MessageBoxW(0, f"Error Fatal GUI: {e}", "Error", 0x10)