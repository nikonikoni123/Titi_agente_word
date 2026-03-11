import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import AgentOrchestrator
from typing import Optional 
import asyncio
import gc
import torch
from contextlib import asynccontextmanager

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_DIR = parent_dir 
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
CERTS_DIR = os.path.join(BASE_DIR, "backend", "certs")

orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    print("------------------------------------------------")
    print(":/ INICIANDO MOTOR TITI (Esto puede tardar)...")
    try:
        orchestrator = AgentOrchestrator()
        orchestrator.get_llm() 
        print(":) MODELO CARGADO EXITOSAMENTE.")
    except Exception as e:
        print(f"!!! ERROR CARGANDO MODELO: {e}")
        import traceback
        traceback.print_exc()
    
    yield 
    
    print("Apagando Titi...")
    if orchestrator:
        orchestrator.cleanup()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health")
def health_check():
    status = "Titi Loaded" if orchestrator else "Loading/Error"
    return {"status": "ok", "agent": status}

class TitiRequest(BaseModel):
    selection: str
    instruction: str
    conversation_id: Optional[str] = None
    mode: str = "academic"

@app.post("/titi")
async def titi_endpoint(data: TitiRequest):
    global orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="El modelo aún se está cargando o falló.")
    try:
        result = await asyncio.to_thread(
            orchestrator.process_titi_task,
            data.selection, 
            data.instruction,
            conversation_id=data.conversation_id,
            mode=data.mode
        )
        return result 
    except Exception as e:
        print(f"Error en endpoint: {e}")
        return {"answer": f"Error interno: {str(e)}", "sources": "", "thought": ""}

@app.get("/conversations")
def list_conversations():
    if not orchestrator: return []
    return orchestrator.get_history_list()

@app.get("/conversations/{cid}")
def get_conversation(cid: str):
    if not orchestrator: raise HTTPException(status_code=503)
    data = orchestrator.get_conversation_details(cid)
    if not data:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return data

@app.delete("/conversations/{cid}")
def delete_conversation(cid: str):
    if not orchestrator: raise HTTPException(status_code=503)
    success = orchestrator.delete_history(cid)
    if not success:
        raise HTTPException(status_code=404, detail="No se pudo eliminar")
    return {"status": "deleted"}

@app.post("/conversations/new")
def new_conversation():
    if not orchestrator: raise HTTPException(status_code=503)
    cid, data = orchestrator.history_manager.create_conversation()
    return {"conversation_id": cid}

if __name__ == "__main__":
    print(f"Iniciando servidor desde: {BASE_DIR}")
    
    cert_file = os.path.join(CERTS_DIR, "cert.pem")
    key_file = os.path.join(CERTS_DIR, "key.pem")
    
    # Generar certificados al vuelo si faltan
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("Generando certificados SSL faltantes...")
        try:
            # Usamos exec para importar el generador usando la ruta corregida
            sys.path.append(os.path.join(BASE_DIR, "backend", "certs"))
            from backend.certs.generar_certificados import generar_certificados_robustos
            os.chdir(CERTS_DIR)
            generar_certificados_robustos()
            os.chdir(BASE_DIR)
        except Exception as e:
            print(f"Advertencia Certificados: {e}")

    uvicorn.run(
        "server:app", 
        host="127.0.0.1", 
        port=8010,
        ssl_keyfile=key_file,   
        ssl_certfile=cert_file,
        log_level="info", 
    )