import os
import time
import shutil
from pathlib import Path

# Sesli mesaj saklama ayarları
VOICE_MESSAGES_DIR = "voice_messages"
MAX_VOICE_DURATION = 25  # saniye
CLEANUP_HOURS = 24  # 24 saat sonra temizle

class VoiceStorage:
    def __init__(self):
        self.ensure_directories()
    
    def ensure_directories(self):
        """Gerekli klasörleri oluştur"""
        os.makedirs(VOICE_MESSAGES_DIR, exist_ok=True)
        print(f"Voice messages directory: {os.path.abspath(VOICE_MESSAGES_DIR)}")
    
    def generate_voice_filename(self, sender, receiver, duration):
        """Ses dosyası için benzersiz isim oluştur"""
        timestamp = int(time.time() * 1000)  # milliseconds
        filename = f"{timestamp}_{sender}_to_{receiver}_{duration}s.wav"
        return filename
    
    def save_voice_message(self, temp_file, sender, receiver, duration):
        """Geçici ses dosyasını kalıcı konuma kaydet"""
        try:
            filename = self.generate_voice_filename(sender, receiver, duration)
            permanent_path = os.path.join(VOICE_MESSAGES_DIR, filename)
            
            # Geçici dosyayı kalıcı konuma kopyala
            shutil.copy2(temp_file, permanent_path)
            
            print(f"Voice message saved: {permanent_path}")
            return permanent_path, filename
            
        except Exception as e:
            print(f"Error saving voice message: {e}")
            return None, None
    
    def get_voice_file_path(self, filename):
        """Ses dosyasının tam yolunu getir"""
        return os.path.join(VOICE_MESSAGES_DIR, filename)
    
    def voice_file_exists(self, filename):
        """Ses dosyasının var olup olmadığını kontrol et"""
        path = self.get_voice_file_path(filename)
        return os.path.exists(path)
    
    def cleanup_old_files(self):
        """Eski ses dosyalarını temizle"""
        try:
            current_time = time.time()
            cleanup_threshold = current_time - (CLEANUP_HOURS * 3600)
            
            cleaned_count = 0
            for filename in os.listdir(VOICE_MESSAGES_DIR):
                if filename.endswith('.wav'):
                    file_path = os.path.join(VOICE_MESSAGES_DIR, filename)
                    file_time = os.path.getctime(file_path)
                    
                    if file_time < cleanup_threshold:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"Cleaned old voice file: {filename}")
            
            if cleaned_count > 0:
                print(f"Cleaned {cleaned_count} old voice files")
                
        except Exception as e:
            print(f"Error during voice file cleanup: {e}")
    
    def get_file_info(self, filename):
        """Dosya bilgilerini getir"""
        try:
            # Dosya adından bilgileri çıkar
            parts = filename.replace('.wav', '').split('_')
            if len(parts) >= 4:
                timestamp = int(parts[0])
                sender = parts[1]
                receiver = parts[3]
                duration = parts[4].replace('s', '')
                
                return {
                    'timestamp': timestamp,
                    'sender': sender,
                    'receiver': receiver,
                    'duration': duration,
                    'filename': filename
                }
        except Exception as e:
            print(f"Error parsing filename {filename}: {e}")
        
        return None

# Global instance
voice_storage = VoiceStorage() 