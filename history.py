import json
import os
import glob
import uuid
from datetime import datetime

class HistoryManager:
    def __init__(self, storage_dir="conversations"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_filepath(self, conversation_id):
        """
        Obtiene la ruta del archivo para una conversación dada.
        """
        return os.path.join(self.storage_dir, f"{conversation_id}.json")

    def create_conversation(self):
        """
        Crea una nueva conversación y devuelve su ID y datos iniciales.
        """
        conversation_id = str(uuid.uuid4())
        data = {
            "id": conversation_id,
            "title": "Nueva investigación",
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        self.save_conversation(conversation_id, data)
        return conversation_id, data

    def save_conversation(self, conversation_id, data):
        """
        Guarda o actualiza una conversación en el almacenamiento.
        """
        filepath = self._get_filepath(conversation_id)
        # Actualizar timestamp
        data["updated_at"] = datetime.now().isoformat()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_conversation(self, conversation_id):
        """
        Carga una conversación desde el almacenamiento.
        """
        filepath = self._get_filepath(conversation_id)
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_conversations(self):
        """
        Lista todas las conversaciones guardadas.
        """
        files = glob.glob(os.path.join(self.storage_dir, "*.json"))
        conversations = []
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    conversations.append({
                        "id": data.get("id"),
                        "title": data.get("title", "Sin título"),
                        "updated_at": data.get("updated_at", "")
                    })
            except:
                continue
        # Ordenar por fecha de actualización descendente
        return sorted(conversations, key=lambda x: x['updated_at'], reverse=True)

    def delete_conversation(self, conversation_id):
        """
        Elimina una conversación del almacenamiento.
        """
        filepath = self._get_filepath(conversation_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def add_message(self, conversation_id, role, content, sources=None, thought=None):
        """
        Añade un mensaje a una conversación existente.
        """
        data = self.load_conversation(conversation_id)
        if not data:
            return None
        
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if sources: msg["sources"] = sources
        if thought: msg["thought"] = thought
        
        data["messages"].append(msg)
        
        # Generar título basado en el primer mensaje de usuario si es "Nueva investigación"
        if len(data["messages"]) == 1 and role == "user":
            data["title"] = content[:40] + "..."
            
        self.save_conversation(conversation_id, data)
        return data