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

if not os.path.exists(STATIC_DIR):
    print(f"ERROR CRÍTICO: No encuentro la carpeta static en: {STATIC_DIR}")
    os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok", "agent": "Titi Loaded"}

print(":/ INICIANDO CARGA PESADA DEL MODELO")
orchestrator = AgentOrchestrator() 
orchestrator.get_llm() 
print(":) MODELO CARGADO. ABRIENDO PUERTOS")

class TitiRequest(BaseModel):
    selection: str
    instruction: str

@app.post("/titi")
async def titi_endpoint(data: TitiRequest):
    try:
        result = orchestrator.process_titi_task(data.selection, data.instruction)
        return result 
    except Exception as e:
        print(f"Error: {e}")
        return {"answer": f"Error interno: {str(e)}", "sources": "", "thought": ""}


if __name__ == "__main__":
    print("INICIANDO SERVIDOR SEGURO EN PUERTO 8010")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8010,
        ssl_keyfile="key.pem",   
        ssl_certfile="cert.pem"  

    )
