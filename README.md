# Titi - Asistente de Investigación Académica (Copilot Local)
### Tu compañero de tesis en Microsoft Word. Rápido, Local y Riguroso.

![Version](https://img.shields.io/badge/version-0.7.2-blue) ![Identity](https://img.shields.io/badge/Identity-Titi_Cabeciblanco-brown) ![Platform](https://img.shields.io/badge/Office-Word_Copilot-blue) ![GPU](https://img.shields.io/badge/GPU-NVIDIA_Required-red)

## Identidad y Propósito

**Titi** no es solo un script; es un agente de investigación diseñado para "vivir" dentro de tu procesador de texto. Su nombre rinde homenaje al **Tití Cabeciblanco**, un primate ágil y pequeño, reflejando la naturaleza de este modelo: **ligero, rápido y capaz de moverse con destreza por grandes volúmenes de información.**

A diferencia de los chats generales, Titi entiende el contexto académico, busca fuentes reales (Papers/PDFs) y cita estrictamente lo que encuentra.

---

## El Problema y La Solución

### El Problema
Los investigadores enfrentan una desconexión crítica: escriben en Word, pero investigan en el navegador. Además, los LLMs genéricos sufren de "alucinaciones" (inventan fuentes) y carecen de un flujo de trabajo integrado. Copiar y pegar entre ventanas rompe la concentración.

### La Solución: Flujo agentico
Titi transforma Word en un entorno de investigación activo. Funciona bajo el paradigma **Selección + Instrucción**:

1.  **Contexto Visual:** Titi "lee" lo que tú seleccionas en el documento.
2.  **Instrucción Dirigida:** Tú le das una orden específica (ej: *"Refuta esta afirmación con papers recientes"* o *"Expande este párrafo citando autores"*).
3.  **Investigación Autónoma:** Titi genera una estrategia de búsqueda, navega la web en busca de PDFs académicos, lee el contenido y sintetiza la respuesta.
4.  **Rigor Académico:** La respuesta incluye citas `[1], [2]` vinculadas a documentos reales encontrados en la sesión.

---

## Arquitectura Técnica

El sistema utiliza una arquitectura híbrida **Cliente-Servidor Local** optimizada para estabilidad:

1.  **Backend (El Cerebro Titi):**
    *   **FastAPI:** Servidor REST con endpoints dedicados (`/titi`, `/health`).
    *   **Lazy Loading (Carga Perezosa):** El modelo no bloquea el inicio del servidor. Carga en memoria solo cuando es necesario o se solicita.
    *   **LLM Local:** Utiliza `NicolasRodriguez/manaba_gemma_2_2b`, optimizado en 4-bits (`bitsandbytes`) para correr en GPUs de consumo.
    *   **RAG Engine:** Motor de Búsqueda y Recuperación que utiliza `DuckDuckGo` filtrando por `filetype:pdf`.

---

## Requisitos del Sistema

Titi corre **localmente** en tu máquina para garantizar privacidad y cero latencias de red externa (salvo para las búsquedas).

### Hardware
*   **Procesador:** Intel i5/Ryzen 5 o superior.
*   **Memoria RAM:** 16 GB recomendado.
*   **GPU (Tarjeta Gráfica):** **CRÍTICO.** Se requiere una GPU **NVIDIA** con al menos **4 GB de VRAM**.
    *   *Sin una GPU NVIDIA, Titi intentará correr en CPU, pero será extremadamente lento.*

### Software
*   **Sistema Operativo:** Windows 10 o Windows 11.
*   **Microsoft Word Online:** 
*   **Python:** 3.10 o superior.

---

## Guía de Instalación

### 1. Instalación Automática script `install.py`.
1.  Haz doble clic en `install.py`.
2.  Acepta los permisos de Administrador.
3.  Espera a que se cree el entorno virtual (`venv`) y se descarguen las librerías.
4.  Se creará un acceso directo en el escritorio llamado **"TITIAgent"** (o Titi Research).

### 2. Configuración en Word

1.	Asegúrate de que tu servidor Python esté corriendo en tu PC.
2.	Word Online no puede conectarse a tu servidor local si el navegador no confía en tu certificado "hecho en casa". Tienes que autorizarlo manualmente antes de abrir Word. Abre el navegador donde usarás Word (Chrome o Edge). Escribe en la barra de direcciones: https://127.0.0.1:8010/health Verás una pantalla roja de advertencia: "La conexión no es privada". Haz clic en Configuración avanzada -> Continuar a 127.0.0.1 (no seguro). Debes ver el texto: {"status": "ok", ...}.
3.	Ingresa a word online y abre un documento en blanco
4.	Busca en la barra superior la sección “Complementos”
5.	Dentro de complementos presiona el botón “Mas complementos”. Selecciona "Mis complementos" Posteriormente, dirígete a la sección “Administrar mis complementos”
6.	Haz clic en "Cargar mi complemento"
7.	Navega la carpeta raíz donde solicitaste a install.py guardar el programa, por defecto viene a la carpeta Documents/TITIAgent y selecciona el archivo manifest.xml.
8.	Se desplegará una pestaña al lateral con el agente listo para usar.

## Desinstalación:
1.	Haz doble clic en `uninstall.py`.
2.	Acepta los permisos de Administrador.
3.	Presiona la letra S en consola para autorizar la desinstalación.
4.	En consola notificara la desinstalación correcta del aplicativo.
### Nota: 
Titi será desinstalado, sin embargo el modelo base manaba/gemma2_2B continuara instalado en usuario/.cache/hugginface/hub localmente, si desea eliminar todos los archivos. Eliminar dicha carpeta.
## Certificados SSL
1.	Los certificados son generados propiamente para ejecución local, para ejecución web o de servidor se debe generar un certificado real.
2.	Si se llegan a extraviar o git no deja descargarlos en el ordenador ejecutar generar_certificados.py 

