import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
from ddgs import DDGS
from history import HistoryManager
import gc
import time

MODEL_ID = "NicolasRodriguez/manaba_gemma_2_2b" 
MAX_DOCS = 12
MAX_HISTORY_TURNS = 6

class LLMEngine:
    """
    Clase para manejar el modelo de lenguaje LLM.
    Carga el modelo y el tokenizador, y proporciona un método para generar texto.
    """
    def __init__(self):
        """
         Inicializa el modelo y el tokenizador.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f":) Titi Cargando en {self.device}...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

        compute_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
        
        
        bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID, 
                quantization_config=bnb_config, 
                device_map=self.device,
                attn_implementation="sdpa"
            )

    def generate(self, prompt, max_tokens=1200):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        input_len = inputs['input_ids'].shape[1]
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=max_tokens,
                temperature=0.4,
                do_sample=True,
                repetition_penalty=1.2,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        generated_tokens = outputs[0][input_len:]
        full_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        """
        if "<start_of_turn>model" in full_text:
            return full_text.split("<start_of_turn>model")[-1].strip()
        return full_text.replace(prompt, "").strip()
        """
        # gestion de vram
        del inputs, outputs
        del generated_tokens
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return full_text.strip()
    
    def unload_model(self):
        print(":/ Liberando modelo y limpiando VRAM...")
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        print(":) VRAM liberada con éxito.")

class AgentOrchestrator:
    """
    Clase para coordinar las operaciones del agente.
    Gestiona la generación de queries, búsquedas web y la formulación de respuestas.
    """
    def __init__(self):
        self.llm = None 
        self.history_manager = HistoryManager()

    def get_llm(self):
        if self.llm is None:
            self.llm = LLMEngine()
        return self.llm

    def _generate_smart_query(self, selection, instruction, history_context="",search_type='academic'):
        """
        Lógica Determinista: Si no hay selección, usa la instrucción directa.
        Esto evita que el modelo pequeño alucine queries malas.
        """
        selection = selection.strip() if selection else ""
        instruction = instruction.strip()
        
        # BÚSQUEDA DIRECTA
        if search_type == 'academic':
            prompt = f"""<start_of_turn>user
Genera una búsqueda corta para Google Scholar.
Historial reciente: {history_context}
Texto base: "{instruction}"
Solo la query, nada más.
Query:<end_of_turn><start_of_turn>model"""
            if selection:
                context = selection[:2600]
                prompt = f"""<start_of_turn>user
Genera una búsqueda corta para Google Scholar.
Historial reciente: {history_context}
Texto base: "{context}"
Intención: "{instruction}"
Solo la query, nada más.
Query:<end_of_turn><start_of_turn>model"""

        else:
            prompt = f"""<start_of_turn>user
Genera una búsqueda corta para jurisprudencia en derecho colombiano y redacción jurídica.
Historial reciente: {history_context}
Texto base: "{instruction}"
Solo la query en español, nada más.
Query:<end_of_turn><start_of_turn>model"""
            if selection:
                context = selection[:2600]
                prompt = f"""<start_of_turn>user
Genera una búsqueda corta para jurisprudencia en derecho colombiano y redacción jurídica.
Historial reciente: {history_context}
Texto base: "{instruction}"
Contexto adicional: "{context}"
Solo la query en español, nada más.
Query:<end_of_turn><start_of_turn>model"""
        try:
            query = self.get_llm().generate(prompt, max_tokens=20)
            print(f"  Query Generada (LLM): {query}", flush=True)
            return f"{query}"
        except:
            return instruction if instruction else "science research paper"
            
        
    def _safe_ddg_search(self, query, max_results=5, max_retries=3):
        """
        Maneja los bloqueos por Rate Limit (HTTP 429) y desconexiones de red.
        """
        for attempt in range(max_retries):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    valid_results =[r for r in results if r.get('body') and len(r.get('body').strip()) > 20]
                    return valid_results
                    
            except Exception as e:
                print(f"  :/ Advertencia de Red: Fallo en DDG (intento {attempt + 1}/{max_retries}). Error: {e}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt
                    print(f"  :/ Esperando {sleep_time} segundos para evadir el bloqueo...")
                    time.sleep(sleep_time)
                else:
                    print("  [!] ERROR CRÍTICO: DuckDuckGo bloqueó la búsqueda temporalmente o no hay conexión.")
                    return []
        return[]

    
    def _search_legal(self, query):
        """
        Búsqueda especializada en SUIN-JURISCOL y Cortes Colombianas.
        """
        print(f":) Titi Buscando (Modo JURÍDICO): {query}")
        context = []
        try:
            ddgs = DDGS()
            # Filtro estricto para SUIN y Altas Cortes
            legal_filters = '(site:suin-juriscol.gov.co OR site:corteconstitucional.gov.co OR site:cortesuprema.gov.co OR site:consejodeestado.gov.co OR site:funcionpublica.gov.co)'
            full_query = f"{query} {legal_filters}"
            
            results = self._safe_ddg_search(full_query, max_results=MAX_DOCS)
            
            for i, r in enumerate(results):
                title = r.get('title', 'Documento Jurídico')
                body = r.get('body', 'Sin resumen.')[:600]
                url = r.get('href', 'N/A')
                
                entry = (
                    f"--- FUENTE JURÍDICA COLOMBIANA [{i+1}] ---\n"
                    f"TÍTULO: {title}\n"
                    f"FUENTE: {url}\n"
                    f"EXTRACTO: {body}...\n"
                )
                context.append(entry)
                
        except Exception as e:
            print(f"Error búsqueda legal: {e}")
            return "No pude conectar con SUIN-JURISCOL."
            
        if not context:
            return "No encontré jurisprudencia o normas exactas en SUIN para esto."
            
        return "\n".join(context)


    def _search_web(self, query):
        """
        Estrategia de Búsqueda Académica usando DuckDuckGo Search (DDGS).
        Aplica filtros específicos para obtener papers y documentos académicos.
        Retorna un string con las fuentes encontradas.
        1. filetype:pdf AND "references"
        2. site:edu OR site:org
        3. site:arxiv.org
        4. Fallback si no hay resultados.
        """
        print(f":) Titi Buscando (Modo Académico): {query}")
        context = []
        try:
            ddgs = DDGS()
            
            academic_filters = 'filetype:pdf -site:academia.edu -site:researchgate.net (site:edu.co OR site:sciencedirect.com OR site:arxiv.org OR site:scielo.org OR site:redalyc.org OR site:dialnet.unirioja.es)'
            full_query = f"{query} {academic_filters}"
            
            # Búsqueda estricta
            results = self._safe_ddg_search(full_query, max_results=MAX_DOCS)
            
            # Si la búsqueda estricta falla, relajamos un poco
            if not results:
                print(":/ Sin resultados estrictos. Relajando filtros...")
                fallback_query = f"{query} research paper filetype:pdf -site:academia.edu -site:researchgate.net"
                results = list(ddgs.text(fallback_query, max_results=MAX_DOCS))

            # Procesamiento de resultados
            for i, r in enumerate(results):
                title = r.get('title', 'Documento Académico')
                # Obtenemos un snippet más largo 500 chars para que la IA tenga mejor contexto
                body = r.get('body', 'Sin resumen disponible.')[:500] 
                url = r.get('href', 'N/A')
                
                # Estructura clara para que el LLM entienda que es una fuente
                entry = (
                    f"--- FUENTE ACADÉMICA [{i+1}] ---\n"
                    f"TÍTULO: {title}\n"
                    f"LINK: {url}\n"
                    f"RESUMEN: {body}...\n"
                )
                context.append(entry)

        # Manejo de errores en la búsqueda
                
        except Exception as e:
            print(f"Error buscando papers: {e}")
            return "No pude conectar a las bases de datos académicas. Verifica tu conexión."
            
        if not context:
            return "No encontré papers relevantes para esta consulta específica."
            
        return "\n".join(context)
    
    def _format_history(self, messages):
        """
        Formatea el historial de mensajes para incluir en el prompt.
        """
        recent = messages[-MAX_HISTORY_TURNS:]
        formatted = ""
        for turn in recent:
            role = "user" if turn['role'] == 'user' else "model"
            formatted += f"<start_of_turn>{role}\n{turn['content']}<end_of_turn>\n"
        return formatted

    def process_titi_task(self, selection, instruction, conversation_id=None, mode='academic'):
        print(":) Titi procesando tarea...")
        if not conversation_id:
            conversation_id, data = self.history_manager.create_conversation()
        else:
            data = self.history_manager.load_conversation(conversation_id)
            if not data:
                conversation_id, data = self.history_manager.create_conversation()
        
        # Agregar el nuevo mensaje al historial
        self.history_manager.add_message(conversation_id,"user", f"{selection}\n\n{instruction}".strip())

        # ultimos 2 mensajes para contexto de busqueda
        history_text = " ".join([m["content"] for m in data["messages"][-2:]])

        # Titi piensa la búsqueda
        search_query = self._generate_smart_query(selection, instruction, history_text, search_type=mode)
        
        # Titi busca en la red
        if mode != 'academic':
            context_data = self._search_legal(search_query)
            history_block = self._format_history(data["messages"][:-1])
            # promt
            final_prompt = f"""<start_of_turn>user
Eres "Titi", un abogado experto en derecho colombiano y redacción jurídica.
Tu tarea es responder a la consulta jurídica basándote ÚNICAMENTE en la jurisprudencia proporcionada.

### NORMATIVA Y JURISPRUDENCIA ENCONTRADA:
"{context_data}"

### TEXTO DEL DOCUMENTO (Contexto):
"{selection}"

### HISTORIAL DE CHAT:
{history_block}

### CONSULTA JURÍDICA:
"{instruction}"

### REGLAS ESTRICTAS DE RESPUESTA:
1. CITAS EXACTAS FORZADAS: Cada argumento debe respaldarse citando el número de la fuente en corchetes al final de la oración. Ejemplo: "La Corte Constitucional protege el derecho fundamental a la salud [1]."
2. FIDELIDAD ABSOLUTA: No inventes leyes, sentencias, ni artículos. Si la información no está en la jurisprudencia encontrada, di explícitamente: "No hay jurisprudencia en los resultados actuales para sustentar esto."
3. LENGUAJE TÉCNICO: Usa jerga jurídica colombiana precisa (ej. exequibilidad, ratio decidendi, cosa juzgada).
4. FORMATO: Responde directamente, sin preámbulos, sin decir "Hola" ni "Aquí tienes el análisis". Listo para pegar en el documento.

Respuesta Jurídica:<end_of_turn>
<start_of_turn>model"""
        
        else:
            context_data = self._search_web(search_query)

            # Guardar la evidencia en el historial
            history_block = self._format_history(data["messages"][:-1])

            # Prompt final Titi
            final_prompt = f"""<start_of_turn>user
Eres "Titi", un asistente de investigación académica avanzado y riguroso.
Tu tarea es responder a la orden del usuario utilizando ÚNICAMENTE la evidencia proporcionada.

### EVIDENCIA ENCONTRADA (Papers y Artículos):
{context_data}

### HISTORIAL DE CHAT:
{history_block}

### TEXTO DEL USUARIO (Contexto base):
"{selection}"

### ORDEN DEL USUARIO:
"{instruction}"
(Si la orden está vacía, analiza y expande el texto académicamente).

### REGLAS ESTRICTAS DE RESPUESTA:
1. RIGOR ABSOLUTO: Usa exclusivamente la información de la "EVIDENCIA ENCONTRADA". Prohibido utilizar conocimiento externo no listado ahí.
2. CITAS EN LÍNEA OBLIGATORIAS: Cada afirmación científica debe terminar con la cita correspondiente usando el número de la fuente en corchetes. Ejemplo: "El cambio climático afecta drásticamente la biodiversidad local [1]." o "Según el autor del documento [2]..."
3. CERO ALUCINACIONES: Prohibido crear URLs, nombres de papers, fechas o autores que no estén explícitamente en la evidencia. Si la evidencia no responde a la orden, escribe: "La literatura encontrada no permite responder a esta solicitud."
4. ESTILO: Tono académico, formal y directo. Sin saludos, sin presentarte. Devuelve el texto estructurado en párrafos listo para una tesis.

Respuesta Académica:<end_of_turn>
<start_of_turn>model
"""
        # Titi genera la respuesta final
        response = self.get_llm().generate(final_prompt, max_tokens=2000)

        # Guardar la respuesta en el historial
        self.history_manager.add_message(conversation_id, "assistant", response, sources=context_data, thought=final_prompt)
        
        return {
            "conversation_id": conversation_id,
            "thought": final_prompt,
            "answer": response,
            "sources": context_data
        }
    def cleanup(self):
        if self.llm is not None:
            self.llm.unload_model()
            self.llm = None

    def get_history_list(self):
        return self.history_manager.list_conversations()
    
    def delete_history(self, cid):
        return self.history_manager.delete_conversation(cid)
    
    def get_conversation_details(self, cid):
        return self.history_manager.load_conversation(cid)

