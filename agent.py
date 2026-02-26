import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
from ddgs import DDGS
from history import HistoryManager

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
        
        
        bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4"
            )
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID, 
                quantization_config=bnb_config, 
                device_map=self.device
            )

    def generate(self, prompt, max_tokens=1200):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        input_len = inputs['input_ids'].shape[1]
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=max_tokens,
                temperature=0.35,
                do_sample=True,
                repetition_penalty=1.2
            )
        
        generated_tokens = outputs[0][input_len:]
        full_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        """
        if "<start_of_turn>model" in full_text:
            return full_text.split("<start_of_turn>model")[-1].strip()
        return full_text.replace(prompt, "").strip()
        """
        return full_text.strip()

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
        else:
            prompt = f"""<start_of_turn>user
Genera una búsqueda corta para jurisprudencia en derecho colombiano y redacción jurídica.
Historial reciente: {history_context}
Texto base: "{instruction}"
Solo la query en español, nada más.
Query:<end_of_turn><start_of_turn>model"""
        if not selection:
            try:
                query = self.get_llm().generate(prompt, max_tokens=50)
                print(f"  Query Generada (LLM): {query}", flush=True)
                return f"{query}"
            except:
                return instruction if instruction else "science research paper"
            
        # BÚSQUEDA CONTEXTUAL
        context = selection[:2600]
        prompt = f"""<start_of_turn>user
Genera una búsqueda corta para Google Scholar.
Historial reciente: {history_context}
Texto base: "{context}"
Intención: "{instruction}"
Solo la query, nada más.
Query:<end_of_turn><start_of_turn>model"""
        
        try:
            query = self.get_llm().generate(prompt, max_tokens=50)
            print(f"  Query Generada (LLM): {query}", flush=True)
            return f"{query}"
        except:
            return "science research paper"

    
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
            
            results = list(ddgs.text(full_query, max_results=4))
            
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
            results = list(ddgs.text(full_query, max_results=MAX_DOCS))
            
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
Rol: Eres "Titi", un abogado experto en derecho colombiano y redacción jurídica.
Tu fuente de verdad es SUIN-JURISCOL.

[CONSULTA]
"{instruction}"

[CONTEXTO DEL DOCUMENTO]
"{selection}"

[JURISPRUDENCIA ENCONTRADA]
{context_data}

[INSTRUCCIONES]
1. Analiza la consulta basándote en la normativa encontrada.
2. Cita los documentos juridicos consjutados específicos, ejemplo: Sentencias (T-123/20).
3. Usa terminología jurídica adecuada (exequibilidad, ratio decidendi, cosa juzgada, etc.).
4. Sé conciso y argumentativo.
5. Devuelve el texto listo y analizado.

Respuesta Jurídica:<end_of_turn>
<start_of_turn>model"""
        
        else:
            context_data = self._search_web(search_query)

            # Guardar la evidencia en el historial
            history_block = self._format_history(data["messages"][:-1])

            # Prompt final Titi
            final_prompt = f"""<start_of_turn>user
Rol: Eres "Titi", un asistente de investigación científica avanzado. Tu nombre rinde homenaje al tití cabeciblanco.
Tu misión es ayudar a redactar documentos con altísimo rigor académico pero siendo directo y útil.

[CONTEXTO DEL USUARIO]
"{selection}"

[HISTORIAL DE CHAT]
{history_block}

[ORDEN DEL USUARIO]
"{instruction}"
(Si la orden está vacía, analiza y mejora el texto académicamente).

[INVESTIGACIÓN REALIZADA (EVIDENCIA)]
{context_data}

[REGLAS DE TITI]
1. Cumple la orden del usuario usando la evidencia encontrada.
2. CITA SIEMPRE las fuentes como [1], [2]. Sin citas, no es ciencia.
3. Mantén un tono académico formal, pero puedes ser muy directo.
4. No menciones "soy una IA", actúa como un colega investigador experto.
5. Devuelve el texto listo para pegar en la tesis.

Respuesta:<end_of_turn>
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

    def get_history_list(self):
        return self.history_manager.list_conversations()
    
    def delete_history(self, cid):
        return self.history_manager.delete_conversation(cid)
    
    def get_conversation_details(self, cid):
        return self.history_manager.load_conversation(cid)

