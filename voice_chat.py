import pyaudio
import wave
import threading
import tempfile
import os
import time

class VoiceRecorder:
    def __init__(self):
        self.chunk = 512  
        self.format = pyaudio.paInt16  # 16-bit ses formatı
        self.channels = 1  # Mono ses
        self.rate = 16000  # 44100'den 16000'e düşür - daha düşük kalite ama küçük dosya
        self.recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        
    def start_recording(self):
        """Ses kaydını başlat"""
        if self.recording:
            return False
            
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.recording = True
            self.frames = []
            
            # Kayıt thread'ini başlat
            self.record_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.record_thread.start()
            
            return True
        except Exception as e:
            print(f"Ses kaydı başlatılamadı: {e}")
            return False
    
    def _record_audio(self):
        """Ses kaydetme döngüsü"""
        while self.recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                print(f"Ses kaydı hatası: {e}")
                break
    
    def stop_recording(self):
        """Ses kaydını durdur ve dosyaya kaydet"""
        if not self.recording:
            return None
            
        self.recording = False
        
        # Thread'in bitmesini bekle
        if hasattr(self, 'record_thread'):
            self.record_thread.join(timeout=1)
        
        # Stream'i kapat
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        
        # Geçici dosyaya kaydet
        temp_file = tempfile.mktemp(suffix='.wav')
        
        try:
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            
            return temp_file
        except Exception as e:
            print(f"Ses dosyası kaydedilemedi: {e}")
            return None
    
    def play_audio(self, filename):
        """Ses dosyasını çal"""
        try:
            with wave.open(filename, 'rb') as wf:
                # Çalma stream'i oluştur
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                # Ses verilerini çal
                data = wf.readframes(self.chunk)
                while data:
                    stream.write(data)
                    data = wf.readframes(self.chunk)
                
                # Stream'i kapat
                stream.stop_stream()
                stream.close()
                
            return True
        except Exception as e:
            print(f"Ses çalınamadı: {e}")
            return False
    
    @staticmethod
    def get_audio_data(filename):
        """Ses dosyasını binary data olarak oku"""
        try:
            with open(filename, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Ses dosyası okunamadı: {e}")
            return None
    
    @staticmethod
    def save_audio_data(data, filename=None):
        """Binary data'yı ses dosyası olarak kaydet"""
        if filename is None:
            filename = tempfile.mktemp(suffix='.wav')
        
        try:
            with open(filename, 'wb') as f:
                f.write(data)
            return filename
        except Exception as e:
            print(f"Ses dosyası kaydedilemedi: {e}")
            return None
    
    def cleanup(self):
        """Kaynakları temizle"""
        if self.recording:
            self.stop_recording()
        
        try:
            self.audio.terminate()
        except:
            pass

# Ses süresi hesaplama fonksiyonu
def get_audio_duration(filename):
    """Ses dosyasının süresini saniye cinsinden döndür"""
    try:
        with wave.open(filename, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return round(duration, 1)
    except:
        return 0

# Test fonksiyonu
def test_voice_recorder():
    """Ses kaydedici test fonksiyonu"""
    recorder = VoiceRecorder()
    
    print("Ses kaydı başlıyor... (5 saniye)")
    if recorder.start_recording():
        time.sleep(5)  # 5 saniye kaydet
        
        filename = recorder.stop_recording()
        if filename:
            print(f"Ses kaydedildi: {filename}")
            print(f"Süre: {get_audio_duration(filename)} saniye")
            
            print("Ses çalınıyor...")
            recorder.play_audio(filename)
            
            # Geçici dosyayı sil
            os.remove(filename)
        else:
            print("Ses kaydı başarısız!")
    else:
        print("Ses kaydı başlatılamadı!")
    
    recorder.cleanup()

if __name__ == "__main__":
    test_voice_recorder() 