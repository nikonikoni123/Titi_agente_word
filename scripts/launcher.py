import sys
import os
import subprocess
import time
import traceback
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import ssl

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
        btn_start.config(state="normal", text=" Iniciar Agente")
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
    root.title("Titi AI")
    root.geometry("400x320")
    
    BG_DARK = "#12142D"
    BG_CARD = "#1C1F43"
    ACCENT = "#FF623D"
    TEXT_MAIN = "#FFFFFF"
    TEXT_MUTED = "#8A8DAB"

    root.configure(bg=BG_DARK)
    root.resizable(False, False)
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width/2) - (400/2))
    y = int((screen_height/2) - (320/2))
    root.geometry(f'400x320+{x}+{y}')

    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure('Start.TButton', font=("Segoe UI", 11, "bold"), background=ACCENT, foreground=TEXT_MAIN, borderwidth=0, padding=12)
    style.map('Start.TButton', background=[('active', '#E55837'), ('disabled', '#3A3347')], foreground=[('disabled', '#706B7D')])

    style.configure('Stop.TButton', font=("Segoe UI", 10, "bold"), background=BG_CARD, foreground=TEXT_MAIN, borderwidth=0, padding=10)
    style.map('Stop.TButton', background=[('active', '#2A2D5C'), ('disabled', '#151733')], foreground=[('disabled', '#4B4F73')])

    top_frame = tk.Frame(root, bg=BG_DARK)
    top_frame.pack(fill=tk.X, pady=(30, 10))
    
    tk.Label(top_frame, text="Titi Engine", font=("Segoe UI", 24, "bold"), bg=BG_DARK, fg=TEXT_MAIN).pack()
    
    lbl_status = tk.Label(top_frame, text="S I S T E M A   D E T E N I D O", font=("Segoe UI", 9, "bold"), bg=BG_DARK, fg="#FF4B4B")
    lbl_status.pack(pady=5)

    tk.Frame(root, bg=ACCENT, height=2).pack(fill=tk.X, padx=40, pady=10)

    bottom_frame = tk.Frame(root, bg=BG_DARK)
    bottom_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

    btn_start = ttk.Button(bottom_frame, text="Iniciar Motor Local", style='Start.TButton', command=start_server)
    btn_start.pack(fill=tk.X, pady=(0, 12))
    
    btn_container = tk.Frame(bottom_frame, bg=BG_DARK)
    btn_container.pack(fill=tk.X)
    
    btn_stop = ttk.Button(btn_container, text="Detener", style='Stop.TButton', command=stop_server, state="disabled")
    btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    btn_open_word = ttk.Button(btn_container, text="Abrir Word", style='Stop.TButton', command=open_word, state="disabled")
    btn_open_word.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def set_ui_state(state):
        if state == "STOPPED":
            lbl_status.config(text="● SISTEMA DETENIDO", fg="#FF4B4B") 
            btn_start.config(state="normal", text="Iniciar Motor Local")
            btn_stop.config(state="disabled")
            btn_open_word.config(state="disabled")
        elif state == "LOADING":
            lbl_status.config(text="CARGANDO MODELO...", fg="#FDE047")
            btn_start.config(state="disabled", text="Asignando VRAM...")
            btn_stop.config(state="normal")
        elif state == "READY":
            lbl_status.config(text="● ONLINE", fg="#10B981") 
            btn_start.config(state="disabled", text="IA Activa")
            btn_stop.config(state="normal")
            btn_open_word.config(state="normal")

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


except Exception as e:
    with open(os.path.join(SCRIPT_DIR, "launcher_error.txt"), "w") as f:
        f.write(traceback.format_exc())
    ctypes.windll.user32.MessageBoxW(0, f"Error Fatal GUI: {e}", "Error", 0x10)