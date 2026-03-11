# Titi - Asistente de Investigación Académica
### Tu compañero de tesis en Microsoft Word. Rápido, Local y Riguroso.

![Version](https://img.shields.io/badge/version-0.8-blue) ![Identity](https://img.shields.io/badge/Identity-Titi_Cabeciblanco-brown) ![Platform](https://img.shields.io/badge/Office-Word_Copilot-blue) ![GPU](https://img.shields.io/badge/GPU-NVIDIA_4GB_Required-red) ![Model](https://img.shields.io/badge/Model-Manaba_Gemma_2B-orange)

## El Dilema de la Investigación Moderna

La investigación académica y jurídica sufre de una fragmentación crónica. El investigador concibe y redacta sus ideas en un procesador de texto, pero se ve forzado a abandonar ese entorno constantemente para cazar fuentes en el navegador. Esta fricción rompe la concentración y el estado de flujo. Por otro lado, la llegada de los Modelos de Lenguaje Grande (LLMs) genéricos introdujo una promesa peligrosa: asistentes que escriben rápido pero que sufren de "alucinaciones", inventando sentencias, autores y fechas con absoluta seguridad. 

El investigador riguroso no necesita un generador de texto creativo o un chatbot conversacional; necesita un asistente analítico, fundamentado en evidencia comprobable y, sobre todo, privado.

De esta necesidad nace **Titi**. Su nombre rinde homenaje al Tití Cabeciblanco, un primate endémico de Colombia conocido por su agilidad y tamaño reducido. Bajo esta misma filosofía biológica, Titi es un agente de Inteligencia Artificial diseñado para ser extremadamente ligero en recursos computacionales, pero capaz de moverse con absoluta destreza a través de la densa selva de la información técnica.

---

## El Factor Diferenciador: Rigor y Privacidad

Titi transforma Microsoft Word en un entorno de investigación activo mediante una arquitectura RAG (Retrieval-Augmented Generation) estrictamente controlada. No dependemos de APIs de terceros ni enviamos tus borradores a la nube. 

1. **Cero Alucinaciones:** Titi opera bajo una directiva de anclaje documental estricta. Si la respuesta no está en los documentos que recuperó de la web durante la búsqueda, no la inventa. Toda afirmación se fundamenta con referencias rastreables al final del párrafo (ej. `[1],[2]`).
2. **Privacidad Total (Local-First):** Tu propiedad intelectual nunca abandona tu máquina. Todo el procesamiento de lenguaje natural y la lectura de tu tesis ocurren en tu propio hardware.
3. **Especialización Dual:** 
   * **Modo Académico:** Filtra y extrae conocimiento exclusivamente de repositorios científicos y universitarios (`.edu.co`, `arxiv`, `scielo`, `redalyc`), priorizando el análisis profundo de archivos PDF.
   * **Modo Jurídico:** Conecta directamente con la jurisprudencia colombiana, rastreando bases de datos de la Corte Constitucional, el Consejo de Estado y SUIN-JURISCOL.

---

## Flujo de Trabajo Agéntico: Selección e Instrucción

El sistema abandona el clásico formato de chat para adoptar un paradigma reactivo incrustado directamente en el documento:

1. **Contextualización Visual:** Seleccionas un texto en tu documento de Word. Titi "lee" silenciosamente ese contexto.
2. **Instrucción Dirigida:** A través del panel lateral, inyectas un comando específico (ej. *"Refuta esta premisa utilizando artículos científicos recientes"* o *"Busca sentencias de tutela que desarrollen este principio"*).
3. **Navegación Autónoma:** El orquestador del agente traduce tu instrucción en consultas de búsqueda optimizadas (evadiendo bloqueos de red), extrae el texto de los documentos fuente en segundo plano y construye un contexto de evidencia sólido.
4. **Síntesis Integrada:** El modelo redacta la argumentación o expansión solicitada, estructurada en un lenguaje formal y lista para ser inyectada en tu documento con un solo clic.

---

## Arquitectura Técnica

Titi no es un simple script, sino un ecosistema Cliente-Servidor desplegado localmente, diseñado meticulosamente para maximizar el rendimiento en hardware de consumo:

* **Cerebro Cognitivo (Modelo Base):** Implementa el modelo `NicolasRodriguez/manaba_gemma_2_2b`. Al ser un modelo optimizado de 2 billones de parámetros, ofrece un equilibrio perfecto entre capacidad de razonamiento lógico y ligereza computacional.
* **Cuantización Extrema:** Utilizando la librería `bitsandbytes`, el modelo se carga dinámicamente en precisión de 4-bits (`nf4`). Esto reduce drásticamente el consumo de memoria VRAM, permitiendo ejecutar inferencia compleja en tarjetas gráficas estándar sin sacrificar la coherencia semántica.
* **Backend de Alto Rendimiento:** Construido sobre `FastAPI` con soporte asíncrono. Implementa un patrón de *Lazy Loading* (carga perezosa); el servidor web inicia en milisegundos, permitiendo que el modelo pesado solo se transfiera a la VRAM en el instante exacto en que se procesa el primer prompt.
* **Frontend Desacoplado:** Una interfaz inyectada directamente en Word a través de la librería `Office.js` y configurada mediante un archivo `manifest.xml`. Desarrollada en HTML/JS puro para garantizar cero dependencias innecesarias y máxima responsividad.

---

## Requisitos del Sistema

Para garantizar una ejecución local fluida y procesamiento en tiempo real, el entorno de despliegue debe cumplir con las siguientes especificaciones:

* **Sistema Operativo:** Windows 10 o Windows 11.
* **Entorno de Trabajo:** Microsoft Word (Online o versión de Escritorio con soporte para complementos web modernos).
* **Capacidad de Procesamiento:** Procesador Intel Core i5 / AMD Ryzen 5 o arquitectura superior. Memoria RAM del sistema de 16 GB (Recomendada).
* **Aceleración de Hardware (Crítico):** Se requiere indispensablemente una **GPU NVIDIA compatible con CUDA** y un mínimo de **4 GB de VRAM dedicada** (ej. GTX 1650, RTX 3050, o superior). *Nota técnica: La ejecución en CPU (Fallback) es posible, pero incurrirá en tiempos de latencia severos.*
* **Dependencias Base:** Python 3.10 o superior instalado en el PATH del sistema.

---

## Guía de Despliegue e Integración

El proyecto incluye rutinas de automatización para reducir la fricción de instalación técnica.

### 1. Construcción del Entorno
1. Ejecuta el script `install.py`.
2. Concede privilegios de administrador. Estos son vitales para modificar las políticas de red (Loopback Exemption) requeridas por la arquitectura de seguridad de Microsoft Office.
3. El instalador provisionará un entorno virtual aislado (`venv`), resolverá las dependencias de PyTorch con soporte CUDA y forjará criptográficamente los certificados SSL locales.
4. Se compilará un acceso directo automatizado ("TITI Agent AI") en el escritorio del usuario.

### 2. Autorización de Certificados (SSL Local)
Office exige un canal de comunicación seguro (HTTPS) estricto. Al ser un servidor alojado localmente en tu red, debes autorizar explícitamente el certificado autofirmado:
1. Inicia el servidor mediante el acceso directo "TITI Agent AI".
2. Navega desde Google Chrome o Microsoft Edge hacia: `https://127.0.0.1:8010/health`
3. El navegador interceptará la conexión advirtiendo sobre la privacidad. Selecciona **Configuración avanzada** y procede hacia **Continuar a 127.0.0.1 (no seguro)**.
4. La validación es exitosa si el endpoint responde con un JSON de estado positivo en tu pantalla.

### 3. Inyección en Microsoft Word
1. Abre un documento en blanco en Microsoft Word.
2. Navega hacia **Insertar** -> **Complementos** -> **Mis complementos**.
3. Selecciona la opción **Cargar mi complemento**.
4. Ubica el archivo `manifest.xml` en el directorio de instalación (por defecto `Documentos/TITIAgent`).
5. El agente Titi se inicializará y anclará en la interfaz lateral de Word, listo para recibir instrucciones.

---

## Mantenimiento y Desinstalación

El ciclo de vida del software está gestionado para mantener la integridad de tu sistema operativo.

* **Retiro del Sistema:** Ejecuta el script `uninstall.py` con privilegios de administrador y confirma presionando `S`. Este proceso revocará los permisos de red, purgará las llaves del registro de Office y destruirá el entorno virtual.
* **Gestión de Caché del Modelo:** El desinstalador retira el aplicativo, pero el modelo fundacional (`manaba_gemma_2_2b`) persiste en la caché global de HuggingFace para evitar descargas redundantes en futuros proyectos de IA. Para liberar este espacio (~2.5 GB), elimina manualmente el directorio alojado en `C:\Users\TU_USUARIO\.cache\huggingface\hub`.
* **Renovación Criptográfica:** Los certificados SSL locales (`cert.pem`, `key.pem`) aseguran la comunicación de origen a destino entre Word y el proceso de Python. Ante cualquier corrupción o expiración, simplemente ejecuta el módulo `backend/certs/generar_certificados.py` para emitir de inmediato un nuevo par de llaves robustas compatibles con la extensión SAN (Subject Alternative Names).

