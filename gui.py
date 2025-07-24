import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog
import json
import os
import socket
import threading
import sys
import file_transfer
import time
import queue
import voice_chat
import voice_storage
import chat_logger


USERS_FILE = 'users.json'
SERVER_HOST = '172.16.1.2'
SERVER_PORT = 6544  # Port değiştirildi

# Kullanıcıları dosyadan oku
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_user(nickname):
    users = load_users()
    for user in users:
        if user['nickname'] == nickname:
            return user
    return None

def save_user(user):
    users = load_users()
    users.append(user)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('Kullanıcı Girişi')
        self.frame = tk.Frame(root)
        self.frame.pack(padx=20, pady=20)
        tk.Label(self.frame, text='Nickname:').grid(row=0, column=0, sticky='e')
        self.nickname_entry = tk.Entry(self.frame)
        self.nickname_entry.grid(row=0, column=1)
        tk.Label(self.frame, text='Şifre (opsiyonel):').grid(row=1, column=0, sticky='e')
        self.password_entry = tk.Entry(self.frame, show='*')
        self.password_entry.grid(row=1, column=1)
        self.login_btn = tk.Button(self.frame, text='Giriş Yap', command=self.login)
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=10)
        self.register_btn = tk.Button(self.frame, text='Kayıt Ol', command=self.open_register)
        self.register_btn.grid(row=3, column=0, columnspan=2, pady=5)
        self.nickname_entry.focus()

    def login(self):
        nickname = self.nickname_entry.get().strip()
        if not nickname:
            messagebox.showerror('Hata', 'Lütfen bir nickname girin!')
            return
        
        user = find_user(nickname)
        if user:
            # Nickname çakışması kontrolü için sunucuya bağlanmayı dene
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(5)
                test_sock.connect((SERVER_HOST, SERVER_PORT))
                test_sock.send(nickname.encode())
                
                # Sunucudan yanıt bekle
                response = test_sock.recv(1024).decode().strip()
                test_sock.close()
                
                if "already taken" in response.lower():
                    messagebox.showerror('Hata', f'Nickname "{nickname}" şu anda kullanımda! Lütfen başka bir nickname deneyin.')
                    return
                else:
                    # Başarılı giriş
                    self.frame.destroy()
                    MainMenuWindow(self.root, user)
            except Exception as e:
                messagebox.showerror('Bağlantı Hatası', f'Sunucuya bağlanılamadı: {e}')
        else:
            messagebox.showerror('Hata', 'Kullanıcı bulunamadı! Önce kayıt olun.')

    def open_register(self):
        RegisterWindow(self.root, self)

class RegisterWindow:
    def __init__(self, root, login_window):
        self.root = root
        self.login_window = login_window
        self.top = tk.Toplevel(root)
        self.top.title('Kayıt Ol')
        self.top.grab_set()
        tk.Label(self.top, text='Ad:').grid(row=0, column=0, sticky='e')
        self.ad_entry = tk.Entry(self.top)
        self.ad_entry.grid(row=0, column=1)
        tk.Label(self.top, text='Soyad:').grid(row=1, column=0, sticky='e')
        self.soyad_entry = tk.Entry(self.top)
        self.soyad_entry.grid(row=1, column=1)
        tk.Label(self.top, text='Nickname:').grid(row=2, column=0, sticky='e')
        self.nickname_entry = tk.Entry(self.top)
        self.nickname_entry.grid(row=2, column=1)
        self.register_btn = tk.Button(self.top, text='Kayıt Ol', command=self.register)
        self.register_btn.grid(row=3, column=0, columnspan=2, pady=10)

    def register(self):
        ad = self.ad_entry.get().strip()
        soyad = self.soyad_entry.get().strip()
        nickname = self.nickname_entry.get().strip()
        if not ad or not soyad or not nickname:
            messagebox.showwarning('Uyarı', 'Lütfen tüm alanları doldurun!')
            return
        if find_user(nickname):
            messagebox.showerror('Hata', 'Bu nickname zaten kayıtlı!')
            return
        user = {
            'ad': ad,
            'soyad': soyad,
            'nickname': nickname,
            'rol': 'user',
            'ip': '',
            'port': 0
        }
        save_user(user)
        messagebox.showinfo('Başarılı', 'Kayıt başarılı! Giriş yapabilirsiniz.')
        self.top.destroy()

class MainMenuWindow:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.frame = tk.Frame(root)
        self.frame.pack(padx=20, pady=20)
        tk.Label(self.frame, text=f'Hoşgeldin, {user["ad"]} {user["soyad"]} ({user["nickname"]})').pack(pady=10)
        tk.Button(self.frame, text='1. Chat', width=20, command=self.open_chat).pack(pady=5)
        tk.Button(self.frame, text='2. File Transfer', width=20, command=self.open_file_transfer).pack(pady=5)
        tk.Button(self.frame, text='3. Kullanıcı Bilgileri', width=20, command=self.show_user_info).pack(pady=5)
        tk.Button(self.frame, text='4. Çıkış', width=20, command=self.root.quit).pack(pady=5)

    def open_chat(self):
        self.frame.destroy()
        ChatWindow(self.root, self.user)

    def open_file_transfer(self):
        self.frame.destroy()
        FileTransferWindow(self.root, self.user)

    def show_user_info(self):
        info = f"Ad: {self.user['ad']}\nSoyad: {self.user['soyad']}\nNickname: {self.user['nickname']}\nRol: {self.user['rol']}\nIP: {self.user['ip']}\nPort: {self.user['port']}"
        messagebox.showinfo('Kullanıcı Bilgileri', info)

class ChatWindow:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.sock = None
        self.running = True
        self.last_user_list_update = 0  # Son kullanıcı listesi güncelleme zamanı
        self.user_list_lock = threading.Lock()  # Kullanıcı listesi güncellemesi için lock
        self.message_queue = queue.Queue()  # Thread-safe mesaj kuyruğu
        
        self.frame = tk.Frame(root)
        self.frame.pack(fill='both', expand=True)
        
        # Kullanıcı listesi paneli
        self.user_listbox = tk.Listbox(self.frame, width=20)
        self.user_listbox.pack(side='left', fill='y', padx=(10,0), pady=10)
        self.user_listbox.bind('<Double-Button-1>', self.open_private_chat)
        
        # Genel chat alanı
        self.text_area = scrolledtext.ScrolledText(self.frame, state='disabled', height=20)
        self.text_area.pack(padx=10, pady=10, fill='both', expand=True, side='left')
        
        # Mesaj giriş frame'i
        input_frame = tk.Frame(self.frame)
        input_frame.pack(padx=10, pady=(0,10), fill='x')
        
        self.entry = tk.Entry(input_frame)
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(input_frame, text='Gönder', command=self.send_message)
        self.send_btn.pack(side='right', padx=(5,0))
        
        self.refresh_btn = tk.Button(self.frame, text='Kullanıcıları Yenile', command=self.refresh_user_list)
        self.refresh_btn.pack(pady=(0,10))
        
        self.back_btn = tk.Button(self.frame, text='Menüye Dön', command=self.back_to_menu)
        self.back_btn.pack(pady=(0,10))
        
        self.connect_to_server()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        
        # İlk kullanıcı listesi güncellemesi 1 saniye sonra
        self.root.after(1000, self.refresh_user_list)
        
        # Queue işleme timer'ı başlat
        self.process_message_queue()

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.sock.send(self.user['nickname'].encode())
        except Exception as e:
            messagebox.showerror('Bağlantı Hatası', f'Sunucuya bağlanılamadı: {e}')
            self.back_to_menu()

    def process_message_queue(self):
        """Ana thread'de queue'daki mesajları işle"""
        try:
            while not self.message_queue.empty():
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'text':
                    self._append_text_safe(data)
                elif msg_type == 'user_list':
                    self._update_user_list_safe(data)
                elif msg_type == 'private_message':
                    sender, target, content = data
                    PrivateChatWindow.show_private_message(target if sender == self.user['nickname'] else sender, 
                                                         sender, content, self.user['nickname'])
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Queue işleme hatası: {e}")
        finally:
            if self.running:
                # 100ms sonra tekrar kontrol et
                self.root.after(100, self.process_message_queue)
    

    
    def _append_text_safe(self, text):
        """Thread-safe text ekleme"""
        try:
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, text)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        except Exception as e:
            print(f"Text ekleme hatası: {e}")
    
    def _update_user_list_safe(self, msg):
        """Thread-safe kullanıcı listesi güncelleme"""
        try:
            userlist = msg.split(':',1)[1].strip().split(',')
            users = []
            for u in userlist:
                u = u.strip()
                if u and u != self.user['nickname'] and u != '/list' and not u.startswith('/'):
                    clean_user = u.split('/')[0].strip()
                    if clean_user and clean_user not in users:
                        users.append(clean_user)
            
            self._update_listbox(users)
        except Exception as e:
            self.message_queue.put(('text', f'Kullanıcı listesi güncellenemedi: {e}\n'))

    def receive_messages(self):
        while self.running:
            try:
                data = self.sock.recv(8192)  # Buffer boyutunu artır
                if not data:
                    self.message_queue.put(('text', 'Sunucu bağlantısı kesildi.\n'))
                    break
                msg = data.decode(errors='ignore')
                
                # Tüm gelen mesajları debug için göster
                if msg.strip() and not msg.strip() == 'PING':
                    print(f"DEBUG: ChatWindow received: {msg[:50]}...")
                
                if msg.strip() == 'PING':
                    self.sock.send(b'PONG\n')
                    continue
                if msg.startswith('USERS:'):
                    # Kullanıcı listesi güncelleme çakışmasını önle
                    current_time = time.time()
                    with self.user_list_lock:
                        # Son güncelleme 2 saniye içindeyse, bu güncellemeyi atla
                        if current_time - self.last_user_list_update > 2:
                            self.message_queue.put(('user_list', msg))
                            self.last_user_list_update = current_time
                    continue
                # Yeni özel mesaj protokolü: PRIVATE|from|to|mesaj
                if msg.startswith('PRIVATE|'):
                    try:
                        _, sender, target, content = msg.strip().split('|', 3)
                        # Sadece bana veya benden gelen özel mesajlar
                        if self.user['nickname'] in (sender, target):
                            self.message_queue.put(('private_message', (sender, target, content)))
                            
                            # Gelen private mesajları da logla (sadece bana gelenler)
                            if target == self.user['nickname']:
                                chat_logger.chat_logger.add_text_message(sender, target, content)
                    except Exception:
                        pass
                    continue
                
                # Yeni ses mesajı protokolü: VOICEMSG_NEW|sender|filename|duration
                if msg.startswith('VOICEMSG_NEW|'):
                    try:
                        print(f"DEBUG: New voice message received")
                        parts = msg.strip().split('|', 3)
                        if len(parts) >= 4:
                            _, sender, filename, duration = parts
                            print(f"DEBUG: Voice message - Sender: {sender}, Filename: {filename}, Duration: {duration}")
                            
                            # Ses dosyasını al ve private chat'te widget olarak göster
                            self._receive_voice_message_new(sender, filename, duration)
                        else:
                            print(f"DEBUG: Invalid VOICEMSG_NEW format")
                    except Exception as e:
                        print(f"DEBUG: Voice message receive error: {e}")
                    continue
                
                # Base64 ses verisi olan uzun mesajları filtrele (fallback)
                if len(msg) > 1000 and ('UklGR' in msg or 'JJWE' in msg):  # Base64 wav header'ları
                    print(f"DEBUG: Filtering out long base64 message: {msg[:50]}...")
                    continue
                
                # Genel mesajlar
                self.message_queue.put(('text', msg))
            except Exception as e:
                self.message_queue.put(('text', f'Hata: {e}\n'))
                break
    
    def _receive_voice_file_immediate(self, filename, duration, sender):
        """VOICEFILE:START sonrası binary mode'da ses dosyası al"""
        try:
            print(f"DEBUG: Starting immediate voice file receive from {sender}")
            
            # Geçici dosya oluştur
            import tempfile
            temp_file = tempfile.mktemp(suffix='.wav')
            
            # Binary mode'da ses dosyası verilerini al
            voice_data = b''
            total_received = 0
            chunks_received = 0
            
            print(f"DEBUG: Reading binary voice data...")
            
            while True:
                try:
                    # Binary veriyi direkt oku (decode etme!)
                    chunk = self.sock.recv(8192)
                    if not chunk:
                        print(f"DEBUG: No more binary data")
                        break
                    
                    chunks_received += 1
                    total_received += len(chunk)
                    print(f"DEBUG: Binary chunk {chunks_received}: {len(chunk)} bytes, total: {total_received}")
                    
                    if b'VOICEFILE:END' in chunk:
                        # End marker'dan önceki kısmı al
                        end_index = chunk.find(b'VOICEFILE:END')
                        if end_index > 0:
                            voice_data += chunk[:end_index]
                            print(f"DEBUG: Added final binary chunk: {end_index} bytes")
                        print(f"DEBUG: Found VOICEFILE:END in binary mode")
                        break
                    else:
                        voice_data += chunk
                        
                except Exception as e:
                    print(f"DEBUG: Error receiving binary voice data: {e}")
                    break
            
            print(f"DEBUG: Binary voice file receive complete, size: {len(voice_data)} bytes")
            
            # WAV header kontrolü
            if len(voice_data) >= 12:
                header = voice_data[:12]
                print(f"DEBUG: WAV header check: {header[:4]} - {header[8:12]}")
                if voice_data[:4] == b'RIFF' and voice_data[8:12] == b'WAVE':
                    print(f"DEBUG: ✅ Valid WAV file header detected")
                else:
                    print(f"DEBUG: ❌ Invalid WAV header")
                    print(f"DEBUG: First 20 bytes: {voice_data[:20]}")
            
            if voice_data and len(voice_data) > 100:  # Minimum dosya boyutu
                # Geçici dosyaya kaydet
                with open(temp_file, 'wb') as f:
                    f.write(voice_data)
                
                print(f"DEBUG: Voice file saved to: {temp_file}")
                
                # Dosya boyutunu kontrol et
                saved_size = os.path.getsize(temp_file)
                print(f"DEBUG: Saved file size: {saved_size} bytes")
                
                # Private chat'e ses mesajını yönlendir
                PrivateChatWindow.show_voice_file(sender, temp_file, duration, self.user['nickname'])
            else:
                print(f"DEBUG: Invalid voice data: size={len(voice_data)}")
                
        except Exception as e:
            print(f"DEBUG: Binary voice file receive error: {e}")
    
    def _receive_voice_message_new(self, sender, filename, duration):
        """Yeni ses mesajı alım sistemi - binary mode"""
        try:
            print(f"DEBUG: Receiving new voice message from {sender}")
            
            # Ses dosyası verilerini al
            voice_data = b''
            total_received = 0
            chunks_received = 0
            
            while True:
                try:
                    chunk = self.sock.recv(8192)
                    if not chunk:
                        print(f"DEBUG: No more binary data")
                        break
                    
                    chunks_received += 1
                    total_received += len(chunk)
                    print(f"DEBUG: Voice chunk {chunks_received}: {len(chunk)} bytes, total: {total_received}")
                    
                    if b'VOICEFILE:END' in chunk:
                        end_index = chunk.find(b'VOICEFILE:END')
                        if end_index > 0:
                            voice_data += chunk[:end_index]
                        print(f"DEBUG: Found VOICEFILE:END in new voice message")
                        break
                    else:
                        voice_data += chunk
                        
                except Exception as e:
                    print(f"DEBUG: Error receiving voice data: {e}")
                    break
            
            print(f"DEBUG: New voice message received, size: {len(voice_data)} bytes")
            
            if voice_data and len(voice_data) > 100:
                # Ses dosyasını kalıcı olarak kaydet
                permanent_path = voice_storage.voice_storage.get_voice_file_path(filename)
                
                with open(permanent_path, 'wb') as f:
                    f.write(voice_data)
                
                print(f"DEBUG: Voice message saved to: {permanent_path}")
                
                # Chat history'ye ekle
                chat_logger.chat_logger.add_voice_message(
                    sender, self.user['nickname'], filename, duration
                )
                
                # Private chat'te widget olarak göster
                PrivateChatWindow.show_voice_widget(sender, filename, duration, self.user['nickname'])
            else:
                print(f"DEBUG: Invalid voice message data: size={len(voice_data)}")
                
        except Exception as e:
            print(f"DEBUG: New voice message receive error: {e}")
    


    def send_message(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            try:
                self.sock.send(msg.encode())
            except:
                self.append_text('Mesaj gönderilemedi.\n')
            self.entry.delete(0, tk.END)

    def append_text(self, text):
        """Mesajı queue'ya ekle (thread-safe)"""
        self.message_queue.put(('text', text))

    def refresh_user_list(self):
        current_time = time.time()
        with self.user_list_lock:
            # Son güncelleme 1 saniye içindeyse, yeni güncelleme yapma
            if current_time - self.last_user_list_update < 1:
                return
            try:
                self.sock.send('/list'.encode())
                self.last_user_list_update = current_time
            except Exception as e:
                self.append_text(f'Kullanıcı listesi alınamadı: {e}\n')


    
    def _update_listbox(self, users):
        """Ana thread'de listbox'ı güncelle"""
        try:
            current_selection = None
            if self.user_listbox.curselection():
                current_selection = self.user_listbox.get(self.user_listbox.curselection()[0])
            
            self.user_listbox.delete(0, tk.END)
            for user in sorted(users):  # Alfabetik sıralama
                self.user_listbox.insert(tk.END, user)
            
            # Önceki seçimi geri yükle
            if current_selection and current_selection in users:
                for i, user in enumerate(users):
                    if user == current_selection:
                        self.user_listbox.selection_set(i)
                        break
        except Exception as e:
            print(f"Listbox güncelleme hatası: {e}")

    def open_private_chat(self, event):
        selection = self.user_listbox.curselection()
        if selection:
            target = self.user_listbox.get(selection[0])
            PrivateChatWindow(self.root, self.user, target, self.sock)

    def back_to_menu(self):
        self.running = False
        
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.frame.destroy()
        MainMenuWindow(self.root, self.user)

class PrivateChatWindow:
    open_chats = dict()  # {other_nickname: window_instance}

    def __init__(self, root, user, other, sock):
        self.root = root
        self.user = user
        self.other = other
        self.sock = sock
        self.message_queue = queue.Queue()  # Thread-safe mesaj kuyruğu
        self.voice_recorder = voice_chat.VoiceRecorder()  # Ses kaydedici
        self.is_recording = False
        
        self.top = tk.Toplevel(root)
        self.top.title(f'Özel Sohbet: {other}')
        
        self.text_area = scrolledtext.ScrolledText(self.top, state='disabled', height=15)
        self.text_area.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Mesaj giriş ve ses kaydetme frame'i
        input_frame = tk.Frame(self.top)
        input_frame.pack(padx=10, pady=(0,10), fill='x')
        
        self.entry = tk.Entry(input_frame)
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.bind('<Return>', self.send_private_message)
        
        self.send_btn = tk.Button(input_frame, text='Gönder', command=self.send_private_message)
        self.send_btn.pack(side='right', padx=(5,0))
        
        # Ses kaydetme butonu
        self.voice_btn = tk.Button(input_frame, text='🎤', command=self.toggle_voice_recording, bg='lightgreen', width=3)
        self.voice_btn.pack(side='right', padx=(5,0))
        
        PrivateChatWindow.open_chats[other] = self
        self.top.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Chat geçmişini yükle
        self.load_chat_history()
        
        # Queue işleme timer'ı başlat
        self.process_message_queue()
    
    def process_message_queue(self):
        """Ana thread'de queue'daki mesajları işle"""
        try:
            while not self.message_queue.empty():
                msg_type, data = self.message_queue.get_nowait()
                if msg_type == 'text':
                    self._append_text_safe(data)
                elif msg_type == 'voice_widget':
                    sender, filename, duration = data
                    self._add_voice_widget(sender, filename, duration)
                elif msg_type == 'voice_file':  # Eski sistem için geriye uyumluluk
                    sender, voice_file, duration = data
                    self._handle_voice_file(sender, voice_file, duration)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"PrivateChat Queue işleme hatası: {e}")
        finally:
            try:
                if self.top.winfo_exists():
                    self.top.after(100, self.process_message_queue)
            except:
                pass
    
    def toggle_voice_recording(self):
        """Ses kaydını başlat/durdur"""
        if not self.is_recording:
            # Kayıt başlat
            if self.voice_recorder.start_recording():
                self.is_recording = True
                self.voice_btn.config(text='⏹️', bg='red')
                self.append_text('🎤 Ses kaydı başladı...\n')
            else:
                messagebox.showerror('Hata', 'Ses kaydı başlatılamadı! Mikrofon erişimi kontrol edin.')
        else:
            # Kayıt durdur
            audio_file = self.voice_recorder.stop_recording()
            self.is_recording = False
            self.voice_btn.config(text='🎤', bg='lightgreen')
            
            if audio_file:
                duration = voice_chat.get_audio_duration(audio_file)
                
                # Duration kontrolleri
                if duration < 0.3:
                    self.append_text(f'⚠️ Ses çok kısa ({duration}s) - Daha uzun kayıt yapın\n')
                    os.remove(audio_file)
                    return
                
                if duration > voice_storage.MAX_VOICE_DURATION:
                    self.append_text(f'⚠️ Ses çok uzun ({duration}s) - Max {voice_storage.MAX_VOICE_DURATION}s olabilir\n')
                    os.remove(audio_file)
                    return
                
                self.append_text(f'🎤 Ses kaydı tamamlandı ({duration}s)\n')
                
                # Ses mesajını gönder
                self.send_voice_message(audio_file, duration)
            else:
                self.append_text('❌ Ses kaydı başarısız!\n')
    
    def send_voice_message(self, audio_file, duration):
        """Ses mesajını file transfer ile gönder"""
        try:
            print(f"DEBUG: Sending voice file to {self.other}")
            print(f"DEBUG: Audio file: {audio_file}, Duration: {duration}")
            
            # Ses dosyasını kalıcı konuma kaydet
            permanent_path, voice_filename = voice_storage.voice_storage.save_voice_message(
                audio_file, self.user['nickname'], self.other, duration
            )
            
            if not permanent_path:
                self.append_text('❌ Ses dosyası kaydedilemedi!\n')
                return
            
            # Chat history'ye ekle
            chat_logger.chat_logger.add_voice_message(
                self.user['nickname'], self.other, voice_filename, duration
            )
            
            # Dosya boyutunu kontrol et
            filesize = os.path.getsize(permanent_path)
            print(f"DEBUG: Voice file size: {filesize} bytes")
            
            if filesize > 2 * 1024 * 1024:  # 2MB limit for voice
                self.append_text('❌ Ses dosyası çok büyük (max 2MB)!\n')
                return
            
            # Sunucuya yeni ses mesajı protokolü ile gönder
            command = f'/sendvoice_new {self.other} {voice_filename} {duration}'
            print(f"DEBUG: Sending command: {command}")
            self.sock.send(command.encode())
            
            # Kısa bekleme
            import time
            time.sleep(0.1)
            
            # Ses dosyasını gönder
            with open(permanent_path, 'rb') as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    self.sock.send(chunk)
            
            # Son işareti gönder
            self.sock.send(b'VOICEFILE:END\n')
            
            self.append_text(f'🎤 Ses mesajı gönderildi ({duration}s)\n')
            print(f"DEBUG: Voice file sent successfully")
            
        except Exception as e:
            print(f"DEBUG: Send voice file error: {e}")
            self.append_text(f'❌ Ses mesajı gönderilemedi: {e}\n')
        finally:
            # Geçici dosyayı sil
            try:
                os.remove(audio_file)
            except:
                pass
    
    def _handle_voice_file(self, sender, voice_file, duration):
        """Gelen ses dosyasını işle ve çal"""
        try:
            print(f"DEBUG: _handle_voice_file - Received voice file from {sender}")
            print(f"DEBUG: _handle_voice_file - Voice file: {voice_file}, Duration: {duration}")
            
            # Ses dosyasının var olduğunu kontrol et
            if not os.path.exists(voice_file):
                print(f"DEBUG: _handle_voice_file - Voice file not found: {voice_file}")
                self.append_text(f'❌ {sender} ses dosyası bulunamadı\n')
                return
            
            # Ses mesajını göster
            self.append_text(f'🔊 {sender} ses mesajı gönderdi ({duration}s)\n')
            
            # Ses dosyasını otomatik çal
            print("DEBUG: _handle_voice_file - Starting audio playback thread")
            threading.Thread(target=self._play_voice_file, args=(voice_file, sender), daemon=True).start()
            
        except Exception as e:
            print(f"DEBUG: _handle_voice_file - Handle voice file error: {e}")
            self.append_text(f'❌ Ses dosyası işlenemedi: {e}\n')
    
    def _add_voice_widget(self, sender, filename, duration):
        """Tıklanabilir ses widget'ı ekle"""
        try:
            print(f"DEBUG: Adding voice widget - Sender: {sender}, Duration: {duration}")
            
            # Widget frame'i oluştur
            widget_frame = tk.Frame(self.text_area.master, bg='lightblue', relief='raised', bd=1)
            
            # Ses mesajı bilgisi
            voice_info = f"🎤 {sender} sesli mesaj ({duration}s)"
            voice_label = tk.Label(widget_frame, text=voice_info, bg='lightblue', font=('Arial', 10))
            voice_label.pack(side='left', padx=5, pady=2)
            
            # Çal butonu
            play_button = tk.Button(
                widget_frame, 
                text='▶️ Çal', 
                command=lambda: self._play_voice_from_widget(filename, sender),
                bg='lightgreen',
                font=('Arial', 9)
            )
            play_button.pack(side='left', padx=5, pady=2)
            
            # Durum label'ı
            status_label = tk.Label(widget_frame, text='Yeni', bg='lightblue', font=('Arial', 8), fg='red')
            status_label.pack(side='right', padx=5, pady=2)
            
            # Widget'ı text area'ya embed et
            self.text_area.config(state='normal')
            self.text_area.window_create(tk.END, window=widget_frame)
            self.text_area.insert(tk.END, '\n')
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
            
            print(f"DEBUG: Voice widget added successfully")
            
        except Exception as e:
            print(f"DEBUG: Error adding voice widget: {e}")
            # Fallback - normal text olarak göster
            self.append_text(f'🎤 {sender} sesli mesaj gönderdi ({duration}s) [Widget hatası]\n')
    
    def _play_voice_from_widget(self, filename, sender):
        """Widget'tan ses çal"""
        try:
            print(f"DEBUG: Playing voice from widget: {filename}")
            
            # Ses dosyası yolunu al
            voice_path = voice_storage.voice_storage.get_voice_file_path(filename)
            
            if not os.path.exists(voice_path):
                self.append_text(f'❌ Ses dosyası bulunamadı: {filename}\n')
                return
            
            # Ses dosyasını çal
            success = self.voice_recorder.play_audio(voice_path)
            
            if success:
                self.append_text(f'✅ Ses çalındı: {sender}\n')
                
                # Chat history'de dinlendi olarak işaretle
                chat_logger.chat_logger.mark_voice_as_played(
                    sender, self.user['nickname'], filename
                )
                print(f"DEBUG: Voice marked as played: {filename}")
            else:
                self.append_text(f'❌ Ses çalınamadı: {filename}\n')
                
        except Exception as e:
            print(f"DEBUG: Error playing voice from widget: {e}")
            self.append_text(f'❌ Ses çalma hatası: {e}\n')
    
    def load_chat_history(self):
        """Chat geçmişini yükle ve göster"""
        try:
            print(f"DEBUG: Loading chat history for {self.user['nickname']} <-> {self.other}")
            
            # Son 20 mesajı getir
            messages = chat_logger.chat_logger.get_chat_messages(
                self.user['nickname'], self.other, limit=20
            )
            
            if messages:
                self.append_text("--- Önceki Mesajlar ---\n")
                
                for message in messages:
                    msg_type = message.get('type')
                    sender = message.get('sender')
                    timestamp = message.get('timestamp', 0)
                    
                    # Tarih formatı
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime('%H:%M')
                    
                    if msg_type == 'text':
                        content = message.get('content', '')
                        if sender == self.user['nickname']:
                            self.append_text(f"[{time_str}] SEN: {content}\n")
                        else:
                            self.append_text(f"[{time_str}] {sender}: {content}\n")
                    
                    elif msg_type == 'voice':
                        filename = message.get('filename', '')
                        duration = message.get('duration', '0')
                        played = message.get('played', False)
                        
                        if sender == self.user['nickname']:
                            self.append_text(f"[{time_str}] SEN: 🎤 Sesli mesaj ({duration}s)\n")
                        else:
                            # Geçmiş ses mesajlarını da widget olarak göster
                            played_text = "✅" if played else "🆕"
                            self.append_text(f"[{time_str}] {sender}: 🎤 Sesli mesaj ({duration}s) {played_text}\n")
                            
                            # Eğer dinlenmemişse widget de ekle
                            if not played and voice_storage.voice_storage.voice_file_exists(filename):
                                self._add_voice_widget(sender, filename, duration)
                
                self.append_text("--- Yeni Mesajlar ---\n")
                print(f"DEBUG: Loaded {len(messages)} messages from history")
            else:
                print(f"DEBUG: No chat history found")
                
        except Exception as e:
            print(f"DEBUG: Error loading chat history: {e}")
            self.append_text("Chat geçmişi yüklenirken hata oluştu.\n")
    
    def _play_voice_file(self, audio_file, sender):
        """Ses dosyasını çal"""
        try:
            print(f"DEBUG: Playing voice file: {audio_file}")
            success = self.voice_recorder.play_audio(audio_file)
            if success:
                print("DEBUG: Voice file playback completed successfully")
                self.append_text(f'✅ Ses çalındı!\n')
            else:
                print("DEBUG: Voice file playback failed")
                self.append_text(f'❌ Ses çalınamadı!\n')
            # Geçici dosyayı sil
            os.remove(audio_file)
            print("DEBUG: Temp voice file deleted")
        except Exception as e:
            print(f"DEBUG: Play voice file error: {e}")
            self.append_text(f'❌ Ses çalma hatası: {e}\n')

    def _append_text_safe(self, text):
        """Thread-safe text ekleme"""
        try:
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, text)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        except Exception as e:
            print(f"PrivateChat text ekleme hatası: {e}")

    def send_private_message(self, event=None):
        msg = self.entry.get().strip()
        if msg:
            try:
                self.sock.send(f'@{self.other} {msg}'.encode())
                
                # Text mesajını chat history'ye ekle
                chat_logger.chat_logger.add_text_message(
                    self.user['nickname'], self.other, msg
                )
                
            except:
                self.message_queue.put(('text', 'Mesaj gönderilemedi.\n'))
            self.entry.delete(0, tk.END)

    def append_text(self, text):
        """Mesajı queue'ya ekle (thread-safe)"""
        self.message_queue.put(('text', text))

    def on_close(self):
        # Ses kaydediciyi temizle
        if hasattr(self, 'voice_recorder'):
            self.voice_recorder.cleanup()
            
        if self.other in PrivateChatWindow.open_chats:
            del PrivateChatWindow.open_chats[self.other]
        self.top.destroy()

    @staticmethod
    def show_private_message(other, sender, content, my_nickname):
        win = PrivateChatWindow.open_chats.get(other)
        if not win:
            # Otomatik pencere aç ve mesajı göster
            for widget in tk._default_root.winfo_children():
                if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
                    try:
                        chat_win = None
                        for child in widget.winfo_children():
                            if hasattr(child, 'user') and hasattr(child, 'sock'):
                                chat_win = child
                                break
                        if chat_win:
                            PrivateChatWindow(widget, chat_win.user, other, chat_win.sock)
                            win = PrivateChatWindow.open_chats.get(other)
                            break
                    except Exception:
                        continue
            if not win:
                messagebox.showinfo('Özel Mesaj', f'{other} ile yeni özel sohbet başlatılamadı.')
                return
        # Mesajı uygun şekilde göster
        if sender == my_nickname:
            win.append_text(f'[SEN]: {content}\n')
        else:
            win.append_text(f'{sender}: {content}\n')
    
    @staticmethod
    def show_voice_widget(sender, filename, duration, my_nickname):
        """Ses mesajını tıklanabilir widget olarak göster"""
        print(f"DEBUG: show_voice_widget - Sender: {sender}, Filename: {filename}, Duration: {duration}")
        win = PrivateChatWindow.open_chats.get(sender)
        if not win:
            print(f"DEBUG: show_voice_widget - No existing chat window for {sender}, creating one")
            # Pencere yoksa oluştur
            for widget in tk._default_root.winfo_children():
                if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
                    try:
                        chat_win = None
                        for child in widget.winfo_children():
                            if hasattr(child, 'user') and hasattr(child, 'sock'):
                                chat_win = child
                                break
                        if chat_win:
                            print(f"DEBUG: show_voice_widget - Creating new private chat window")
                            PrivateChatWindow(widget, chat_win.user, sender, chat_win.sock)
                            win = PrivateChatWindow.open_chats.get(sender)
                            break
                    except Exception as e:
                        print(f"DEBUG: show_voice_widget - Error creating window: {e}")
                        continue
            if not win:
                print(f"DEBUG: show_voice_widget - Could not create/find window for {sender}")
                return
        
        print(f"DEBUG: show_voice_widget - Adding voice widget to queue")
        # Ses widget'ını queue'ya ekle
        win.message_queue.put(('voice_widget', (sender, filename, duration)))

class FileTransferWindow:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.sock = None
        self.running = True
        self.message_queue = queue.Queue()  # Thread-safe mesaj kuyruğu
        
        self.frame = tk.Frame(root)
        self.frame.pack(fill='both', expand=True)
        
        self.text_area = scrolledtext.ScrolledText(self.frame, state='disabled', height=15)
        self.text_area.pack(padx=10, pady=10, fill='both', expand=True)
        
        self.select_btn = tk.Button(self.frame, text='Dosya Seç ve Gönder', command=self.send_file_dialog)
        self.select_btn.pack(pady=5)
        
        self.target_entry = tk.Entry(self.frame)
        self.target_entry.pack(padx=10, pady=5, fill='x')
        self.target_entry.insert(0, 'Hedef kullanıcı nickname')
        
        self.back_btn = tk.Button(self.frame, text='Menüye Dön', command=self.back_to_menu)
        self.back_btn.pack(pady=5)
        
        self.connect_to_server()
        threading.Thread(target=self.receive, daemon=True).start()
        
        # Queue işleme timer'ı başlat
        self.process_message_queue()

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.sock.send(self.user['nickname'].encode())
        except Exception as e:
            messagebox.showerror('Bağlantı Hatası', f'Sunucuya bağlanılamadı: {e}')
            self.back_to_menu()

    def process_message_queue(self):
        """Ana thread'de queue'daki mesajları işle"""
        try:
            while not self.message_queue.empty():
                msg_type, data = self.message_queue.get_nowait()
                if msg_type == 'text':
                    self._append_text_safe(data)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"FileTransfer Queue işleme hatası: {e}")
        finally:
            if self.running:
                self.root.after(100, self.process_message_queue)
    
    def _append_text_safe(self, text):
        """Thread-safe text ekleme"""
        try:
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, text)
            self.text_area.see(tk.END)
            self.text_area.config(state='disabled')
        except Exception as e:
            print(f"FileTransfer text ekleme hatası: {e}")

    def append_text(self, text):
        """Mesajı queue'ya ekle (thread-safe)"""
        self.message_queue.put(('text', text))

    def send_file_dialog(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        target = self.target_entry.get().strip()
        if not target or target == 'Hedef kullanıcı nickname':
            messagebox.showwarning('Uyarı', 'Lütfen hedef kullanıcı nickname girin!')
            return
        filename = os.path.basename(filepath)
        if not file_transfer.is_file_valid(filepath):
            messagebox.showerror('Hata', f'Dosya bulunamadı veya boyut limiti aşıldı ({file_transfer.MAX_SIZE} bytes).')
            return
        filesize = file_transfer.get_file_size(filepath)
        try:
            # Sunucuya dosya gönderme komutu
            self.sock.send(f'/sendfile {target} {filename}'.encode())
            # Sunucudan onay beklemeden dosyayı gönderiyoruz (protokol gereği)
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(file_transfer.BUFFER_SIZE)
                    if not chunk:
                        break
                    self.sock.send(chunk)
            self.sock.send(b'FILE:END\n')
            self.append_text(f'{filename} dosyası {target} kullanıcısına gönderildi.\n')
        except Exception as e:
            self.append_text(f'Dosya gönderilemedi: {e}\n')

    def receive(self):
        file_receiving = False
        file_info = None
        file_buffer = b''
        received_size = 0
        while self.running:
            try:
                data = self.sock.recv(8192)  # Buffer boyutunu artır
                if not data:
                    self.message_queue.put(('text', 'Sunucu bağlantısı kesildi.\n'))
                    break
                msg = data.decode(errors='ignore')
                if msg.strip() == 'PING':
                    self.sock.send(b'PONG\n')
                    continue
                if not file_receiving and data.startswith(b'FILE:START'):
                    header = data.decode(errors='ignore').strip().split()
                    if len(header) >= 4:
                        _, filename, filesize, sender = header[0:4]
                        filesize = int(filesize)
                        self.message_queue.put(('text', f'Gelen dosya: {filename} ({filesize} bytes) Gönderen: {sender}\n'))
                        file_info = {'filename': f'received_{filename}', 'filesize': filesize}
                        file_receiving = True
                        received_size = 0
                        file_buffer = b''
                    continue
                if file_receiving:
                    if b'FILE:END' in data:
                        end_index = data.find(b'FILE:END')
                        file_buffer += data[:end_index]
                        received_size += len(data[:end_index])
                        with open(file_info['filename'], 'wb') as f:
                            f.write(file_buffer)
                        self.message_queue.put(('text', f'Dosya kaydedildi: {file_info["filename"]} ({received_size} bytes)\n'))
                        file_receiving = False
                        file_info = None
                        file_buffer = b''
                        received_size = 0
                        continue
                    else:
                        file_buffer += data
                        received_size += len(data)
                        if received_size >= file_info['filesize']:
                            with open(file_info['filename'], 'wb') as f:
                                f.write(file_buffer)
                            self.message_queue.put(('text', f'Dosya kaydedildi: {file_info["filename"]} ({received_size} bytes)\n'))
                            file_receiving = False
                            file_info = None
                            file_buffer = b''
                            received_size = 0
                            continue
                        continue
                self.message_queue.put(('text', data.decode(errors='ignore')))
            except Exception as e:
                self.message_queue.put(('text', f'Hata: {e}\n'))
                break

    def back_to_menu(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.frame.destroy()
        MainMenuWindow(self.root, self.user)

if __name__ == '__main__':
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop() 