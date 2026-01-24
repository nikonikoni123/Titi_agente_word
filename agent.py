import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
from ddgs import DDGS

MODEL_ID = "NicolasRodriguez/manaba_gemma_2_2b" 
MAX_DOCS = 4

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

    def get_llm(self):
        if self.llm is None:
            self.llm = LLMEngine()
        return self.llm

    def _generate_smart_query(self, selection, instruction):
        """
        Lógica Determinista: Si no hay selección, usa la instrucción directa.
        Esto evita que el modelo pequeño alucine queries malas.
        """
        selection = selection.strip() if selection else ""
        instruction = instruction.strip()
        
        # BÚSQUEDA DIRECTA

        if not selection:
            prompt = f"""<start_of_turn>user
Genera una búsqueda corta para Google Scholar.
Texto base: "{instruction}"
Solo la query, nada más.
Query:<end_of_turn><start_of_turn>model"""
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
            
            academic_filters = '(filetype:pdf "references") OR site:edu OR site:sciencedirect.com OR site:arxiv.org'
            full_query = f"{query} {academic_filters}"
            
            # Búsqueda estricta
            results = list(ddgs.text(full_query, max_results=MAX_DOCS))
            
            # Si la búsqueda estricta falla, relajamos un poco
            if not results:
                print(":/ Sin resultados estrictos. Relajando filtros...")
                fallback_query = f"{query} research paper filetype:pdf"
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

    def process_titi_task(self, selection, instruction):
        print(":) Titi procesando tarea...")
        
        # Titi piensa la búsqueda
        search_query = self._generate_smart_query(selection, instruction)
        
        # Titi busca en la red
        context_data = self._search_web(search_query)

        # Prompt final Titi
        final_prompt = f"""<start_of_turn>user
Rol: Eres "Titi", un asistente de investigación científica avanzado. Tu nombre rinde homenaje al tití cabeciblanco.
Tu misión es ayudar a redactar documentos con altísimo rigor académico pero siendo directo y útil.

[CONTEXTO DEL USUARIO]
"{selection}"

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
        
        return {
            "thought": final_prompt,
            "answer": response,
            "sources": context_data
        }

