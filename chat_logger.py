import json
import os
import time
from datetime import datetime

CHAT_LOGS_DIR = "chat_logs"

class ChatLogger:
    def __init__(self):
        self.ensure_directories()
    
    def ensure_directories(self):
        """Gerekli klasörleri oluştur"""
        os.makedirs(CHAT_LOGS_DIR, exist_ok=True)
        print(f"Chat logs directory: {os.path.abspath(CHAT_LOGS_DIR)}")
    
    def get_chat_filename(self, user1, user2):
        """İki kullanıcı arası sohbet dosya adını oluştur"""
        # Alfabetik sıralama ile tutarlılık sağla
        users = sorted([user1.lower(), user2.lower()])
        filename = f"{users[0]}_{users[1]}.json"
        return os.path.join(CHAT_LOGS_DIR, filename)
    
    def load_chat_history(self, user1, user2):
        """Chat geçmişini yükle"""
        chat_file = self.get_chat_filename(user1, user2)
        
        if os.path.exists(chat_file):
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading chat history: {e}")
        
        # Yeni chat dosyası oluştur
        return {
            "participants": [user1, user2],
            "created": time.time(),
            "messages": []
        }
    
    def save_chat_history(self, user1, user2, chat_data):
        """Chat geçmişini kaydet"""
        try:
            chat_file = self.get_chat_filename(user1, user2)
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def add_text_message(self, sender, receiver, content):
        """Text mesajı ekle"""
        chat_data = self.load_chat_history(sender, receiver)
        
        message = {
            "type": "text",
            "sender": sender,
            "content": content,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        }
        
        chat_data["messages"].append(message)
        self.save_chat_history(sender, receiver, chat_data)
        print(f"Text message logged: {sender} -> {receiver}")
    
    def add_voice_message(self, sender, receiver, filename, duration):
        """Sesli mesaj ekle"""
        chat_data = self.load_chat_history(sender, receiver)
        
        message = {
            "type": "voice",
            "sender": sender,
            "filename": filename,
            "duration": duration,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "played": False  # Dinlenip dinlenmediği
        }
        
        chat_data["messages"].append(message)
        self.save_chat_history(sender, receiver, chat_data)
        print(f"Voice message logged: {sender} -> {receiver} ({duration}s)")
    
    def mark_voice_as_played(self, sender, receiver, filename):
        """Sesli mesajı dinlendi olarak işaretle"""
        chat_data = self.load_chat_history(sender, receiver)
        
        for message in chat_data["messages"]:
            if (message.get("type") == "voice" and 
                message.get("filename") == filename):
                message["played"] = True
                break
        
        self.save_chat_history(sender, receiver, chat_data)
        print(f"Voice message marked as played: {filename}")
    
    def get_unplayed_voice_messages(self, user1, user2, for_user):
        """Belirli kullanıcı için dinlenmemiş sesli mesajları getir"""
        chat_data = self.load_chat_history(user1, user2)
        unplayed = []
        
        for message in chat_data["messages"]:
            if (message.get("type") == "voice" and 
                message.get("sender") != for_user and
                not message.get("played", False)):
                unplayed.append(message)
        
        return unplayed
    
    def get_chat_messages(self, user1, user2, limit=50):
        """Son N mesajı getir"""
        chat_data = self.load_chat_history(user1, user2)
        messages = chat_data.get("messages", [])
        
        # Son mesajları getir
        return messages[-limit:] if len(messages) > limit else messages
    
    def cleanup_old_chats(self, days=30):
        """Eski sohbetleri temizle"""
        try:
            current_time = time.time()
            cleanup_threshold = current_time - (days * 24 * 3600)
            
            for filename in os.listdir(CHAT_LOGS_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(CHAT_LOGS_DIR, filename)
                    file_time = os.path.getctime(file_path)
                    
                    if file_time < cleanup_threshold:
                        os.remove(file_path)
                        print(f"Cleaned old chat log: {filename}")
                        
        except Exception as e:
            print(f"Error during chat log cleanup: {e}")

# Global instance
chat_logger = ChatLogger() 