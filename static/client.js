let lastSelection = "";
// CAMBIO CRÍTICO: Usar IP explícita, no localhost
const SERVER_URL = "https://127.0.0.1:8010"; 

Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        // Mensaje de diagnóstico inicial
        console.log("🐵 Titi Conectado. Host: Word.");
        
        // 1. INTENTAR REGISTRAR EVENTO (Método rápido)
        try {
            Office.context.document.addHandlerAsync(
                Office.EventType.DocumentSelectionChanged, 
                onSelectionChange,
                (result) => {
                    if (result.status === Office.AsyncResultStatus.Failed) {
                        console.error("Falló registro de eventos:", result.error.message);
                    }
                }
            );
        } catch (e) {
            console.error("Error crítico registrando eventos:", e);
        }

        // 2. ACTIVAR POLLING (Método seguro - Respaldo)
        // Por si el evento falla o Word se duerme, revisamos cada 1.5s
        setInterval(checkSelectionContext, 1500);

        // Chequeo inicial
        checkSelectionContext();
        
        // Poner foco en el input
        setTimeout(() => {
            const input = document.getElementById("user-input");
            if(input) input.focus();
        }, 500);
    } else {
        // Si se abre en navegador web para pruebas
        console.log("Modo Navegador Web (Pruebas).");
        document.getElementById("context-text").innerText = "Modo Pruebas (Fuera de Word)";
    }
});

function onSelectionChange(eventArgs) {
    checkSelectionContext();
}

// Lógica de lectura de contexto
async function checkSelectionContext() {
    try {
        await Word.run(async (context) => {
            const selection = context.document.getSelection();
            selection.load("text");
            await context.sync();
            
            const pill = document.getElementById("context-pill");
            const txt = document.getElementById("context-text");
            // Limpieza de texto segura
            const textContent = selection.text ? selection.text.trim() : "";
            
            // Solo actualizamos si la selección cambió realmente para evitar parpadeo
            if (textContent !== lastSelection && textContent.length > 0) {
                lastSelection = textContent;
                
                if(pill && txt) {
                    pill.className = "context-pill active";
                    let displayTxt = textContent.length > 25 
                        ? textContent.substring(0, 25) + "..." 
                        : textContent;
                    txt.innerText = `Analizando: "${displayTxt}"`;
                }
            } else if (textContent.length === 0) {
                 // Si está vacío, solo actualizamos si antes teníamos algo
                 if (lastSelection !== "") {
                     lastSelection = "";
                     if(pill && txt) {
                        pill.className = "context-pill";
                        txt.innerText = "Esperando selección...";
                     }
                 }
            }
        });
    } catch(e) {
        // No mostramos error aquí para no saturar, pero lo logueamos
        console.log("Word no está listo o error de lectura:", e);
    }
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const text = input.value.trim();
    
    if (!text && !lastSelection) {
        if(input) {
            input.style.borderColor = "red";
            setTimeout(() => input.style.borderColor = "#E0E0E0", 500);
        }
        return;
    }

    if(text) appendMessage("msg-user", text);
    
    if(input) {
        input.value = "";
        input.style.height = "24px";
    }
    setLoading(true);

    const instruction = text || "Analiza esto académicamente.";
    
    // Verificar si estamos en modo "Contexto" (pill activa) o modo "Chat General"
    const pill = document.getElementById("context-pill");
    const hasContext = pill && pill.classList.contains("active");
    const contextToSend = hasContext ? lastSelection : "";

    try {
        // CAMBIO: Usamos la constante SERVER_URL definida arriba (127.0.0.1)
        const response = await fetch(`${SERVER_URL}/titi`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                selection: contextToSend, 
                instruction: instruction 
            })
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const data = await response.json();
        appendMessage("msg-agent", data, true);

    } catch (error) {
        // DIAGNÓSTICO VISIBLE EN EL CHAT
        let errorMsg = "No puedo conectar con Titi (127.0.0.1:8010).";
        
        if (error.message.includes("Failed to fetch")) {
            errorMsg += "<br><b>Posibles causas:</b><br>1. El Launcher está cerrado.<br>2. El antivirus bloqueó Python.<br>3. Windows bloqueó la conexión (Ejecuta FIX_CONNECTION.bat).";
        } else {
            errorMsg += `<br>Detalle: ${error.message}`;
        }
        
        appendMessage("msg-agent", `🙈 <b>Error:</b> ${errorMsg}`);
        console.error(error);
    } finally {
        setLoading(false);
        if(input) input.focus();
    }
}

// --- UTILIDADES UI ---
function appendMessage(cls, content, showAction = false) {
    const container = document.getElementById("chat-container");
    if(!container) return;

    const div = document.createElement("div");
    div.className = `message ${cls}`;
    
    let htmlContent = "";

    // SI EL CONTENIDO ES UN OBJETO (Respuesta de Titi)
    if (typeof content === 'object' && content !== null) {
        
        // 1. SECCIÓN: CADENA DE PENSAMIENTO (Desplegable superior)
        if (content.thought) {
            htmlContent += `
                <details style="margin-bottom: 8px; border: 1px solid #e0e0e0; border-radius: 6px; background: #fff;">
                    <summary style="cursor: pointer; padding: 6px; font-size: 10px; color: #999; font-weight: 600; list-style: none;">
                        Cadena de pensamiento
                    </summary>
                    <div style="padding: 8px; font-size: 10px; color: #666; font-family: monospace; white-space: pre-wrap; background: #f9f9f9; border-top: 1px solid #eee;">
                        ${content.thought.replace(/</g, "&lt;")}
                    </div>
                </details>
            `;
        }

        // 2. SECCIÓN: RESPUESTA PRINCIPAL
        let mainText = (content.answer || "")
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        htmlContent += `<div style="font-size: 13px; color: #2c3e50;">${mainText}</div>`;

        // 3. SECCIÓN: REFERENCIAS (Desplegable inferior)
        if (content.sources && !content.sources.includes("No pude conectar")) {
            htmlContent += `
                <details style="margin-top: 12px; border-top: 1px solid #eee; padding-top: 5px;">
                    <summary style="cursor: pointer; font-size: 11px; color: #D35400; font-weight: 600;">
                        Referencias Consultadas
                    </summary>
                    <div style="margin-top: 5px; font-size: 10px; color: #555; line-height: 1.4; padding: 5px; background: #FFF0E6; border-radius: 4px;">
                        ${content.sources.replace(/\n/g, "<br>")}
                    </div>
                </details>
            `;
        }

        // Botón de pegar en tesis (usamos la respuesta limpia)
        if (showAction) {
            const safeText = encodeURIComponent(content.answer);
            htmlContent += `
                <div style="margin-top:10px;"></div>
                <div class="insert-btn" onclick="insertText('${safeText}')">
                    Pegar en Word
                </div>
            `;
        }

    } else {
        // SI ES TEXTO SIMPLE (Mensaje del usuario o error)
        htmlContent = (content || "").replace(/\n/g, "<br>");
    }

    div.innerHTML = htmlContent;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function setLoading(isLoading) {
    const loader = document.getElementById("loader");
    const btn = document.getElementById("send-btn");
    
    if(loader) loader.style.display = isLoading ? "block" : "none";
    if(btn) btn.disabled = isLoading;
}

function handleEnter(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function insertText(encodedText) {
    const textToInsert = decodeURIComponent(encodedText);
    await Word.run(async (context) => {
        const selection = context.document.getSelection();
        selection.insertText(textToInsert, Word.InsertLocation.replace);
        await context.sync();
    });

}
