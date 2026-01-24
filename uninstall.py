import os
import shutil
import winreg
import ctypes
import sys
import subprocess
import time

# ==========================================
#   CONFIGURACIÓN DESINSTALADOR TITI AI
# ==========================================
INSTALL_DIR_NAME = "TITIAgent"
SHORTCUT_NAME = "TITI Agent.lnk" # Asegúrate que coincida con el instalador

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_install_path():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.join(docs, INSTALL_DIR_NAME)

def kill_running_process():
    """
    Intenta detener procesos de python que puedan estar corriendo desde esa carpeta.
    Es un intento básico para liberar los archivos antes de borrar.
    """
    print(":) Verificando si el agente está en ejecución...")
    # No podemos matar todo "python.exe" porque afectaríamos otros programas.
    # Simplemente advertimos o intentamos un cierre suave si detectamos bloqueo.
    pass 

def clean_loopback_exemption():
    """
    Elimina los permisos de red que se dieron para WebView2.
    """
    print(":) Limpiando reglas de red (Loopback Exemption)...")
    app_ids = [
        "Microsoft.Win32WebViewHost_cw5n1h2txyewy",
        "Microsoft.Office.Desktop_8wekyb3d8bbwe"
    ]
    
    for app_id in app_ids:
        try:
            # El flag -d elimina la regla
            cmd = ["CheckNetIsolation.exe", "LoopbackExempt", "-d", f"-n={app_id}"]
            subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    print(":) Reglas de red eliminadas.")

def remove_desktop_shortcut():
    print(":) Buscando accesos directos...")
    
    # Rutas posibles
    user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    public_desktop = os.path.join(os.environ.get('PUBLIC', 'C:\\Users\\Public'), 'Desktop')
    
    deleted = False
    for desktop in [user_desktop, public_desktop]:
        lnk_path = os.path.join(desktop, SHORTCUT_NAME)
        if os.path.exists(lnk_path):
            try:
                os.remove(lnk_path)
                print(f"   - Eliminado: {lnk_path}")
                deleted = True
            except Exception as e:
                print(f"   - No se pudo borrar {lnk_path}: {e}")
    
    if not deleted:
        print("   - No se encontraron accesos directos.")

def unregister_word_addin():
    print(":) Eliminando registro de Word...")
    target_uuid = "d8d8d8d8-d8d8-d8d8-d8d8-d8d8d8d8d8d8"
    parent_path = rf"Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{{{target_uuid}}}"
    
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_path)
        print(":) Registro limpiado exitosamente.")
    except FileNotFoundError:
        print(":) El registro ya estaba limpio.")
    except Exception as e:
        print(f":/ Advertencia: No se pudo borrar la clave del registro: {e}")

def remove_installation_files():
    target_dir = get_install_path()
    
    if os.path.exists(target_dir):
        print(f":) Eliminando archivos en: {target_dir}")
        print("   Espere un momento, borrando entorno virtual y modelos...")
        
        try:
            # Función para manejar archivos de solo lectura (común en git o venv)
            def remove_readonly(func, path, excinfo):
                os.chmod(path, 0o777)
                func(path)
            
            shutil.rmtree(target_dir, onerror=remove_readonly)
            print(":) Carpeta eliminada correctamente.")
            
        except OSError as e:
            print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(" NO SE PUDO BORRAR LA CARPETA COMPLETA")
            print(" Causas probables:")
            print(" 1. El Agente Titi sigue abierto.")
            print(" 2. Tienes un archivo abierto dentro de la carpeta.")
            print(f" Error: {e}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(" -> Por favor, cierra la ventana negra del servidor y borra la carpeta 'TITIAgent' en Documentos manualmente.")
    else:
        print(":) La carpeta de instalación no existe.")

def main():
    print("""
    ========================================
       DESINSTALADOR TITI AI
    ========================================
    """)
    print("Este proceso eliminará el Agente, el modelo de IA y la configuración de Word.")
    
    confirm = input("\n¿Estás seguro? (escribe S si/ N No): ")
    if confirm.lower() != 's':
        print("Cancelado.")
        return

    # 1. Limpieza de Red (Nuevo)
    clean_loopback_exemption()

    # 2. Accesos Directos
    remove_desktop_shortcut()
    
    # 3. Registro de Word
    unregister_word_addin()
    
    # 4. Archivos (Lo más pesado al final)
    remove_installation_files()
    
    print("\n========================================")
    print("   DESINSTALACIÓN FINALIZADA")
    print("========================================")
    print("Si la pestaña sigue apareciendo en Word, simplemente reinicia tu PC.")
    input("\nPresiona ENTER para cerrar.")

if __name__ == "__main__":
    if not is_admin():
        print("Solicitando permisos de administrador para limpiar el sistema...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        main()