let lastSelection = "";
let currentConversationId = null;
const SERVER_URL = "https://127.0.0.1:8010"; 

Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        console.log("Titi Conectado con Memoria.");
        setupUI(); 
        loadHistoryList(); 
        
        try {
            Office.context.document.addHandlerAsync(
                Office.EventType.DocumentSelectionChanged, 
                onSelectionChange
            );
        } catch(e) { console.error(e); }
        
        setInterval(checkSelectionContext, 1500);
        checkSelectionContext();
    }
});


function setupUI() {
    const header = document.querySelector('.header');
    if (header && !document.getElementById('history-btn')) {
        const btn = document.createElement('button');
        btn.id = 'history-btn';
        btn.innerHTML = 'Tus chats';
        btn.style.cssText = "background:none; border:none; font-size:18px; cursor:pointer; margin-right:10px;";
        btn.onclick = toggleHistoryPanel;
        header.insertBefore(btn, header.lastElementChild);
    }

    // Crear panel lateral de historial
    if (!document.getElementById('history-panel')) {
        const panel = document.createElement('div');
        panel.id = 'history-panel';
        panel.style.cssText = `
            position: fixed; top: 60px; left: -250px; width: 240px; bottom: 0;
            background: #fff; border-right: 1px solid #ddd; z-index: 100;
            transition: left 0.3s; padding: 10px; overflow-y: auto; box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        `;
        
        panel.innerHTML = `
            <button onclick="startNewChat()" style="width:100%; padding:8px; background:#D35400; color:white; border:none; border-radius:4px; cursor:pointer; margin-bottom:10px;"> Nuevo Chat</button>
            <div id="history-list">Cargando...</div>
        `;
        document.body.appendChild(panel);
    }
}

function toggleHistoryPanel() {
    const panel = document.getElementById('history-panel');
    const isOpen = panel.style.left === '0px';
    panel.style.left = isOpen ? '-250px' : '0px';
    if (!isOpen) loadHistoryList();
}

async function loadHistoryList() {
    try {
        const res = await fetch(`${SERVER_URL}/conversations`);
        const list = await res.json();
        const container = document.getElementById('history-list');
        container.innerHTML = "";

        list.forEach(item => {
            const div = document.createElement('div');
            div.style.cssText = "padding: 8px; border-bottom: 1px solid #eee; cursor: pointer; font-size: 12px;";
            div.innerHTML = `
                <div style="font-weight:bold; color:#333;">${item.title}</div>
                <div style="color:#999; font-size:10px;">${new Date(item.updated_at).toLocaleDateString()}</div>
                <button onclick="deleteChat(event, '${item.id}')" style="float:right; border:none; background:none; color:red; cursor:pointer;">Delete</button>
            `;
            div.onclick = () => loadConversation(item.id);
            container.appendChild(div);
        });
    } catch(e) { console.error("Error cargando historial", e); }
}

async function startNewChat() {
    currentConversationId = null;
    document.getElementById("chat-container").innerHTML = `
        <div class="message msg-agent">
            ¡Hola de nuevo! Soy Titi. Empecemos una nueva investigación.
        </div>
    `;
    toggleHistoryPanel();
    
    try {
        const res = await fetch(`${SERVER_URL}/conversations/new`, { method: "POST" });
        const data = await res.json();
        currentConversationId = data.conversation_id;
    } catch(e) {}
}

async function loadConversation(id) {
    try {
        const res = await fetch(`${SERVER_URL}/conversations/${id}`);
        const data = await res.json();
        currentConversationId = data.id;
        
        const container = document.getElementById("chat-container");
        container.innerHTML = ""; 
        
        // Reconstruir chat
        data.messages.forEach(msg => {
            if (msg.role === 'user') {
                let display = msg.content;
                appendMessage("msg-user", display);
            } else {
                appendMessage("msg-agent", {
                    answer: msg.content,
                    sources: msg.sources || "",
                    thought: msg.thought || ""
                }, true);
            }
        });
        
        toggleHistoryPanel(); 
    } catch(e) { console.error(e); }
}

async function deleteChat(e, id) {
    e.stopPropagation(); 
    if(!confirm("¿Borrar esta conversación?")) return;
    
    await fetch(`${SERVER_URL}/conversations/${id}`, { method: "DELETE" });
    loadHistoryList();
    if(currentConversationId === id) startNewChat();
}


async function sendMessage() {
    const input = document.getElementById("user-input");
    const text = input.value.trim();
    
    if (!text && !lastSelection) return;
    if(text) appendMessage("msg-user", text);
    
    if(input) input.value = "";
    setLoading(true);

    const pill = document.getElementById("context-pill");
    const hasContext = pill && pill.classList.contains("active");
    const contextToSend = hasContext ? lastSelection : "";

    try {
        const response = await fetch(`${SERVER_URL}/titi`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                selection: contextToSend, 
                instruction: text || "Analiza esto.",
                conversation_id: currentConversationId 
            })
        });

        const data = await response.json();
        
        if (data.conversation_id) currentConversationId = data.conversation_id;
        
        appendMessage("msg-agent", data, true);

    } catch (error) {
        appendMessage("msg-agent", `🙈 Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}
function onSelectionChange(eventArgs) { checkSelectionContext(); }
async function checkSelectionContext() {
    try {
        await Word.run(async (context) => {
            const selection = context.document.getSelection();
            selection.load("text");
            await context.sync();
            const pill = document.getElementById("context-pill");
            const txt = document.getElementById("context-text");
            const textContent = selection.text ? selection.text.trim() : "";
            if (textContent !== lastSelection && textContent.length > 0) {
                lastSelection = textContent;
                if(pill && txt) {
                    pill.className = "context-pill active";
                    let displayTxt = textContent.length > 25 ? textContent.substring(0, 25) + "..." : textContent;
                    txt.innerText = `Analizando: "${displayTxt}"`;
                }
            } else if (textContent.length === 0 && lastSelection !== "") {
                 lastSelection = "";
                 if(pill && txt) { pill.className = "context-pill"; txt.innerText = "Esperando selección..."; }
            }
        });
    } catch(e) {}
}
function appendMessage(cls, content, showAction = false) {
    const container = document.getElementById("chat-container");
    if(!container) return;
    const div = document.createElement("div");
    div.className = `message ${cls}`;
    let htmlContent = "";
    if (typeof content === 'object' && content !== null) {
        if (content.thought) {
            htmlContent += `<details style="margin-bottom:8px; border:1px solid #e0e0e0; border-radius:6px; background:#fff;"><summary style="cursor:pointer; padding:6px; font-size:10px; color:#999;">Cadena de pensamiento</summary><div style="padding:8px; font-size:10px; color:#666; font-family:monospace; white-space:pre-wrap;">${content.thought.replace(/</g, "&lt;")}</div></details>`;
        }
        let mainText = (content.answer || "").replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        htmlContent += `<div style="font-size:13px; color:#2c3e50;">${mainText}</div>`;
        if (content.sources && !content.sources.includes("No pude conectar")) {
            htmlContent += `<details style="margin-top:12px; border-top:1px solid #eee; padding-top:5px;"><summary style="cursor:pointer; font-size:11px; color:#D35400;">Referencias</summary><div style="margin-top:5px; font-size:10px; color:#555; background:#FFF0E6; border-radius:4px; padding:5px;">${content.sources.replace(/\n/g, "<br>")}</div></details>`;
        }
        if (showAction) {
            const safeText = encodeURIComponent(content.answer);
            htmlContent += `<div style="margin-top:10px;"></div><div class="insert-btn" onclick="insertText('${safeText}')">Pegar en Word</div>`;
        }
    } else {
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
async function insertText(encodedText) {
    const textToInsert = decodeURIComponent(encodedText);
    await Word.run(async (context) => {
        const selection = context.document.getSelection();
        selection.insertText(textToInsert, Word.InsertLocation.replace);
        await context.sync();
    });
}
function handleEnter(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }
function autoResize(el) { el.style.height = '24px'; el.style.height = Math.min(el.scrollHeight, 80) + 'px'; }

