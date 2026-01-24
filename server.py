import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import AgentOrchestrator
import os

print("""
========================================
   MONITOR DE SISTEMA - TITI AI
========================================
""", flush=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Verificación de seguridad
if not os.path.exists(STATIC_DIR):
    print(f"ERROR CRÍTICO: No encuentro la carpeta static en: {STATIC_DIR}")
    # Creamos la carpeta para evitar crash, pero el usuario debe llenarla
    os.makedirs(STATIC_DIR, exist_ok=True)

# 1. Crear la APP
app = FastAPI()

# Configuración CORS (Permitir todas las conexiones para desarrollo local)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Endpoint
@app.get("/health")
def health_check():
    # Si este endpoint responde, significa que el servidor ya arrancó
    # y por ende, el modelo ya cargó.
    return {"status": "ok", "agent": "Titi Loaded"}

# 4. CARGA DEL MODELO
# El script se detendrá aquí descargando cargando la IA.
# Uvicorn NO iniciará hasta que esta línea termine.
print(":/ INICIANDO CARGA PESADA DEL MODELO")
orchestrator = AgentOrchestrator() 
# Forzamos la carga del motor inmediatamente para bloquear el puerto hasta estar listos
orchestrator.get_llm() 
print(":) MODELO CARGADO. ABRIENDO PUERTOS")

class TitiRequest(BaseModel):
    selection: str
    instruction: str

@app.post("/titi")
async def titi_endpoint(data: TitiRequest):
    try:
        # Ahora result es un diccionario {thought, answer, sources}
        result = orchestrator.process_titi_task(data.selection, data.instruction)
        return result 
    except Exception as e:
        print(f"Error: {e}")
        return {"answer": f"Error interno: {str(e)}", "sources": "", "thought": ""}


if __name__ == "__main__":
    # CAMBIO CRÍTICO: Activamos SSL (HTTPS)
    print("🔒 INICIANDO SERVIDOR SEGURO (HTTPS) EN PUERTO 8010")
    print("⚠️  IMPORTANTE: La primera vez el navegador te dará una advertencia de seguridad.")
    print("    Debes darle a 'Configuración avanzada' -> 'Continuar a 127.0.0.1 (no seguro)'.")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8010,
        ssl_keyfile="key.pem",   # Llave privada
        ssl_certfile="cert.pem"  # Certificado público
    )