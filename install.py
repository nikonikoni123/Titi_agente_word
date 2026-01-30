import os
import sys
import shutil
import subprocess
import ctypes
import winreg
import logging
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN DEL PROYECTO
# ==============================================================================
APP_NAME = "TITI Agent AI"
INSTALL_FOLDER_NAME = "TITIAgent"
SHORTCUT_NAME = "TITI Agent.lnk"
LOG_FILE = "install_log.txt"

REQUIRED_FILES = {
    "launcher.py": ".",
    "server.py": ".",
    "agent.py": ".",
    "uninstall.py": ".",
    "manifest.xml": ".",
    "cert.pem":".",
    "key.pem":".",
    "history.py":".",
    "generar_certificados.py": ".",
    "sidebar.html": "static",
    "client.js": "static"
}

DEFAULT_REQUIREMENTS = """--extra-index-url https://download.pytorch.org/whl/cu121
fastapi
uvicorn
python-multipart
huggingface_hub
torch
torchvision
torchaudio
transformers
sentence-transformers
ctransformers[cuda]
accelerate
bitsandbytes
pywin32
winshell
ddgs
cryptography
"""

# ==============================================================================
# UTILIDADES
# ==============================================================================
def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger('').addHandler(console)

def log_step(msg):
    print(f"\n[+] {msg}")
    logging.info(f"STEP: {msg}")

def log_error(msg, exc=None):
    print(f"\n[!] ERROR: {msg}")
    logging.error(msg)
    if exc:
        logging.error(exc, exc_info=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    if not is_admin():
        log_step("Solicitando permisos de administrador...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception as e:
            log_error("Fallo al elevar permisos.", e)
        sys.exit(0)

def get_install_paths():
    user_docs = Path(os.path.expanduser("~")) / "Documents" / INSTALL_FOLDER_NAME
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        desktop_str, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        desktop = Path(desktop_str)
    except:
        desktop = Path(os.path.expanduser("~")) / "Desktop"
    return user_docs, desktop

# ==============================================================================
# INSTALACIÓN
# ==============================================================================
def find_source_file(filename):
    cwd = Path.cwd()
    f = cwd / filename
    if f.exists(): return f
    for child in cwd.iterdir():
        if child.is_dir():
            f = child / filename
            if f.exists(): return f
    return None

def copy_files(dest_dir: Path):
    log_step("Copiando archivos...")
    if not dest_dir.exists(): dest_dir.mkdir(parents=True)
    (dest_dir / "static").mkdir(exist_ok=True)
    
    missing = []
    for filename, rel_target in REQUIRED_FILES.items():
        src = find_source_file(filename)
        if src:
            try:
                shutil.copy2(src, dest_dir / rel_target / filename)
            except Exception as e:
                log_error(f"Error copiando {filename}", e)
                missing.append(filename)
        else:
            missing.append(filename)
            
    # Requirements
    req_src = find_source_file("requirements.txt")
    if req_src:
        shutil.copy2(req_src, dest_dir / "requirements.txt")
    else:
        with open(dest_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(DEFAULT_REQUIREMENTS)

    if missing:
        raise FileNotFoundError(f"Faltan archivos: {', '.join(missing)}")

def setup_python_env(dest_dir: Path):
    log_step("Configurando entorno virtual (venv)...")
    venv_dir = dest_dir / "venv"
    pip_exe = venv_dir / "Scripts" / "pip.exe"
    
    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    
    log_step("Instalando dependencias...")
    try:
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([str(pip_exe), "install", "-r", str(dest_dir / "requirements.txt")])
    except subprocess.CalledProcessError:
        raise Exception("Fallo en la instalación PIP. Revisa log.")

def configure_system(dest_dir: Path):
    log_step("Configurando sistema (Red y Registro)...")
    apps = ["Microsoft.Win32WebViewHost_cw5n1h2txyewy", "Microsoft.Office.Desktop_8wekyb3d8bbwe"]
    for app in apps:
        subprocess.run(["CheckNetIsolation.exe", "LoopbackExempt", "-a", f"-n={app}"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    CATALOG_ID = "d8d8d8d8-d8d8-d8d8-d8d8-d8d8d8d8d8d8"
    reg_path = rf"Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{{{CATALOG_ID}}}"
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        winreg.SetValueEx(key, "Id", 0, winreg.REG_SZ, CATALOG_ID)
        winreg.SetValueEx(key, "Url", 0, winreg.REG_SZ, str(dest_dir))
        winreg.SetValueEx(key, "Flags", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except Exception as e:
        logging.warning(f"Error registro: {e}")

# ==============================================================================
# FUNCIÓN CRÍTICA: ACCESO DIRECTO (PowerShell File Method)
# ==============================================================================
def create_shortcut_powershell(dest_dir: Path, desktop_dir: Path):
    log_step("Creando acceso directo (Método PowerShell File)...")
    
    # 1. Definir rutas exactas
    # Intentamos usar pythonw.exe (sin consola), si no existe, python.exe
    python_target = dest_dir / "venv" / "Scripts" / "pythonw.exe"
    if not python_target.exists():
        logging.warning("pythonw.exe no encontrado, usando python.exe")
        python_target = dest_dir / "venv" / "Scripts" / "python.exe"
        
    launcher_script = dest_dir / "launcher.py"
    lnk_path = desktop_dir / SHORTCUT_NAME
    icon_path = dest_dir / "venv" / "Scripts" / "python.exe"

    # 2. Crear script .ps1 temporal
    # Usamos comillas simples para envolver las rutas en el PS script
    ps_script_path = dest_dir / "create_shortcut.ps1"
    
    ps_content = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{str(lnk_path)}')
    $Shortcut.TargetPath = '{str(python_target)}'
    $Shortcut.Arguments = '"{str(launcher_script)}"'
    $Shortcut.WorkingDirectory = '{str(dest_dir)}'
    $Shortcut.Description = 'Iniciar Agente IA'
    $Shortcut.IconLocation = '{str(icon_path)},0'
    $Shortcut.Save()
    """
    
    try:
        # Escribir el archivo .ps1
        with open(ps_script_path, "w", encoding="utf-8") as f:
            f.write(ps_content)
            
        # Ejecutarlo con ExecutionPolicy Bypass
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"PowerShell falló: {result.stderr}")
            
        logging.info(f"Acceso directo creado: {lnk_path}")
        print(f"   -> Acceso directo OK: {lnk_path}")
        
    except Exception as e:
        log_error("No se pudo crear acceso directo.", e)
        print("\n   [!] ALTERNATIVA MANUAL:")
        print(f"   Por favor crea un acceso directo a: {python_target}")
        print(f"   Y pon en argumentos: \"{launcher_script}\"")
        
    finally:
        # Limpieza
        if ps_script_path.exists():
            try:
                os.remove(ps_script_path)
            except: pass

def main():
    if os.name == 'nt': os.system('cls')
    setup_logging()
    
    print("=== INSTALADOR TITI AI (Versión Estable) ===")
    elevate_privileges()
    
    try:
        dest, desk = get_install_paths()
        copy_files(dest)
        setup_python_env(dest)
        configure_system(dest)
        create_shortcut_powershell(dest, desk)
        
        print("\n" + "="*40)
        print(" ✅ INSTALACIÓN FINALIZADA")
        print("="*40)
        print(f"Carpeta: {dest}")
        print(f"Log: {os.path.abspath(LOG_FILE)}")
        
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        logging.critical("Fallo total", exc_info=True)
        
    input("\nPresiona ENTER para salir.")

if __name__ == "__main__":
    main()