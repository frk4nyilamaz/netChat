import socket
import threading
import chat_core
import file_transfer
import os
import time
import base64
import re

HOST = '172.16.1.2'
PORT = 6544  # Port değiştirildi
PING_INTERVAL = 10  
PING_TIMEOUT = 20   

last_pong = {}  # {nickname: last_pong_timestamp}


def send_user_list():
    userlist = ', '.join(chat_core.get_userlist())
    msg = f'USERS: {userlist}\n'.encode()
    for sock in chat_core.get_clients().values():
        try:
            sock.send(msg)
        except:
            pass


def ping_clients():
    while True:
        time.sleep(PING_INTERVAL)
        now = time.time()
        to_remove = []
        for nickname in list(chat_core.get_userlist()):
            sock = chat_core.get_socket_by_nickname(nickname)
            if not sock:
                continue
            try:
                sock.send(b'PING\n')
            except:
                to_remove.append(nickname)
                continue
            # Zaman aşımı kontrolü
            if nickname in last_pong and now - last_pong[nickname] > PING_TIMEOUT:
                to_remove.append(nickname)
        for nickname in to_remove:
            sock = chat_core.get_socket_by_nickname(nickname)
            if sock:
                try:
                    sock.close()
                except:
                    pass
            chat_core.remove_client(nickname)
            chat_core.broadcast(f'{nickname} left the chat!')
            if nickname in last_pong:
                del last_pong[nickname]
        # Her ping döngüsünde kullanıcı listesi değişmiş olabilir, güncelle
        send_user_list()


def handle_client(client_socket):
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    nickname = None
    try:
        # Nickname sorgusu kaldırıldı, ilk gelen veri nickname olarak alınacak
        nickname = client_socket.recv(1024).decode().strip()
        
        # Nickname geçerlilik kontrolü
        retry_count = 0
        while (not nickname or chat_core.is_nickname_taken(nickname) or 
               nickname == '*' or len(nickname) < 2) and retry_count < 3:
            client_socket.send('Nickname already taken or invalid. Try again: \n'.encode())
            nickname = client_socket.recv(1024).decode().strip()
            retry_count += 1
            
        # 3 deneme sonrası hala geçersizse bağlantıyı kes
        if not nickname or chat_core.is_nickname_taken(nickname) or nickname == '*':
            client_socket.send('Too many invalid attempts. Connection closed.\n'.encode())
            return
            
        chat_core.add_client(nickname, client_socket)
        last_pong[nickname] = time.time()
        client_socket.send(f'Welcome, {nickname}!\n'.encode())
        chat_core.broadcast(f'{nickname} joined the chat!', client_socket)
        send_user_list()
        
        while True:
            try:
                # Büyük ses mesajları için buffer boyutunu artır
                data = client_socket.recv(8192)  # Buffer boyutunu artır
                if not data:
                    break
                message = data.decode(errors='ignore').strip()
                
                # Eğer mesaj tam gelmemişse (ses mesajı gibi), devamını oku
                if message.startswith('/voice ') and not re.search(r' \d+\.\d+$', message):
                    # Duration ile bitmeyen ses mesajı - devamını oku
                    attempts = 0
                    while attempts < 10:  # Sonsuz döngüyü önle
                        try:
                            additional_data = client_socket.recv(8192)
                            if not additional_data:
                                break
                            additional_message = additional_data.decode(errors='ignore').strip()
                            message += additional_message
                            # Duration pattern kontrolü (X.X formatında)
                            if re.search(r' \d+\.\d+$', message):
                                break
                            attempts += 1
                        except Exception as e:
                            print(f"DEBUG: Error reading additional voice data: {e}")
                            break
                
                if message == 'PONG':
                    last_pong[nickname] = time.time()
                    continue
                if message == '/exit':
                    break
                if message == '/list':
                    userlist = ', '.join(chat_core.get_userlist())
                    client_socket.send(f'USERS: {userlist}\n'.encode())
                    continue
                if message.startswith('/sendfile '):
                    try:
                        _, target, filename = message.split(' ', 2)
                        target_sock = chat_core.get_socket_by_nickname(target)
                        if not target_sock:
                            client_socket.send('User not found.\n'.encode())
                            continue
                        if not file_transfer.is_file_valid(filename):
                            client_socket.send(f'File not found or exceeds {file_transfer.MAX_SIZE} bytes.\n'.encode())
                            continue
                        filesize = file_transfer.get_file_size(filename)
                        target_sock.send(f'FILE:START {filename} {filesize} {nickname}\n'.encode())
                        client_socket.send(f'Sending {filename} to {target}...\n'.encode())
                        with open(filename, 'rb') as f:
                            while True:
                                chunk = f.read(file_transfer.BUFFER_SIZE)
                                if not chunk:
                                    break
                                target_sock.send(chunk)
                        target_sock.send(b'FILE:END\n')
                        client_socket.send(f'File {filename} sent to {target}.\n'.encode())
                    except Exception as e:
                        client_socket.send(f'File transfer failed: {e}\n'.encode())
                    continue
                
                # Ses dosyası transferi protokolü: /sendvoice target filename duration
                if message.startswith('/sendvoice '):
                    try:
                        print(f"DEBUG: Voice file transfer from {nickname}")
                        parts = message.split(' ', 3)
                        if len(parts) >= 4:
                            _, target, filename, duration = parts
                            print(f"DEBUG: Target: {target}, Filename: {filename}, Duration: {duration}")
                            
                            target_sock = chat_core.get_socket_by_nickname(target)
                            if not target_sock:
                                client_socket.send('User not found.\n'.encode())
                                continue
                            
                            # Alıcıya ses dosyası transferi başlıyor bilgisi
                            target_sock.send(f'VOICEFILE:START {filename} {duration} {nickname}\n'.encode())
                            client_socket.send(f'Sending voice file to {target}...\n'.encode())
                            print(f"DEBUG: Voice file transfer started")
                            
                            # Ses dosyası verilerini bekle ve aktar
                            voice_data = b''
                            total_received = 0
                            while True:
                                try:
                                    chunk = client_socket.recv(8192)
                                    if not chunk:
                                        print(f"DEBUG: No more data from client")
                                        break
                                    
                                    total_received += len(chunk)
                                    print(f"DEBUG: Received chunk: {len(chunk)} bytes, total: {total_received}")
                                    
                                    if b'VOICEFILE:END' in chunk:
                                        # End marker'dan önceki kısmı al
                                        end_index = chunk.find(b'VOICEFILE:END')
                                        if end_index > 0:
                                            voice_data += chunk[:end_index]
                                        print(f"DEBUG: Found VOICEFILE:END marker at position {end_index}")
                                        break
                                    else:
                                        voice_data += chunk
                                        
                                except Exception as e:
                                    print(f"DEBUG: Error receiving voice data: {e}")
                                    break
                            
                            print(f"DEBUG: Voice data received, size: {len(voice_data)} bytes")
                            
                            # WAV header kontrolü
                            if len(voice_data) >= 4:
                                header = voice_data[:4]
                                print(f"DEBUG: Voice file header: {header}")
                                if header != b'RIFF':
                                    print(f"DEBUG: WARNING - Invalid WAV header: {header}")
                            
                            # Ses dosyasını alıcıya gönder
                            if voice_data:
                                target_sock.send(voice_data)
                                target_sock.send(b'VOICEFILE:END\n')
                                print(f"DEBUG: Sent {len(voice_data)} bytes to target")
                            else:
                                print(f"DEBUG: No voice data to send")
                            
                            client_socket.send(f'Voice file sent to {target} ({duration}s)\n'.encode())
                            print(f"DEBUG: Voice file transfer completed")
                        else:
                            client_socket.send('Invalid voice file command format.\n'.encode())
                    except Exception as e:
                        print(f"DEBUG: Voice file transfer error: {e}")
                        client_socket.send(f'Voice file transfer failed: {e}\n'.encode())
                    continue
                
                # Yeni ses mesajı protokolü: /sendvoice_new target filename duration  
                if message.startswith('/sendvoice_new '):
                    try:
                        print(f"DEBUG: New voice message from {nickname}")
                        parts = message.split(' ', 3)
                        if len(parts) >= 4:
                            _, target, filename, duration = parts
                            print(f"DEBUG: Target: {target}, Filename: {filename}, Duration: {duration}")
                            
                            target_sock = chat_core.get_socket_by_nickname(target)
                            if not target_sock:
                                client_socket.send('User not found.\n'.encode())
                                continue
                            
                            # Alıcıya ses mesajı bilgisi gönder (artık otomatik çalmayacak)
                            voice_notification = f'VOICEMSG_NEW|{nickname}|{filename}|{duration}\n'
                            target_sock.send(voice_notification.encode())
                            client_socket.send(f'Sending voice message to {target}...\n'.encode())
                            print(f"DEBUG: Voice message notification sent")
                            
                            # Ses dosyası verilerini bekle ve aktar
                            voice_data = b''
                            total_received = 0
                            while True:
                                try:
                                    chunk = client_socket.recv(8192)
                                    if not chunk:
                                        print(f"DEBUG: No more data from client")
                                        break
                                    
                                    total_received += len(chunk)
                                    
                                    if b'VOICEFILE:END' in chunk:
                                        # End marker'dan önceki kısmı al
                                        end_index = chunk.find(b'VOICEFILE:END')
                                        if end_index > 0:
                                            voice_data += chunk[:end_index]
                                        print(f"DEBUG: Found VOICEFILE:END marker")
                                        break
                                    else:
                                        voice_data += chunk
                                        
                                except Exception as e:
                                    print(f"DEBUG: Error receiving voice data: {e}")
                                    break
                            
                            print(f"DEBUG: Voice data received, size: {len(voice_data)} bytes")
                            
                            # Ses dosyasını alıcıya gönder
                            if voice_data:
                                target_sock.send(voice_data)
                                target_sock.send(b'VOICEFILE:END\n')
                                print(f"DEBUG: Sent {len(voice_data)} bytes to target")
                            
                            client_socket.send(f'Voice message sent to {target} ({duration}s)\n'.encode())
                            print(f"DEBUG: New voice message transfer completed")
                        else:
                            client_socket.send('Invalid voice message command format.\n'.encode())
                    except Exception as e:
                        print(f"DEBUG: New voice message error: {e}")
                        client_socket.send(f'Voice message failed: {e}\n'.encode())
                    continue
                if message.startswith('@'):
                    try:
                        target, priv_msg = message[1:].split(' ', 1)
                        target_sock = chat_core.get_socket_by_nickname(target)
                        if target_sock:
                            private_msg = f'PRIVATE|{nickname}|{target}|{priv_msg}\n'.encode()
                            target_sock.send(private_msg)
                            client_socket.send(private_msg)
                        else:
                            client_socket.send('User not found.\n'.encode())
                    except ValueError:
                        client_socket.send('Use: @nickname message\n'.encode())
                    continue
                

                
                chat_core.broadcast(f'[{nickname}]: {message}', client_socket)
            except ConnectionResetError:
                print(f"Client {nickname} disconnected unexpectedly")
                break
            except socket.error as e:
                print(f"Socket error for {nickname}: {e}")
                break
            except Exception as e:
                print(f"Unexpected error for {nickname}: {e}")
                break
                
    except ConnectionResetError:
        print(f"Client disconnected during handshake")
    except socket.error as e:
        print(f"Socket error during handshake: {e}")
    except Exception as e:
        print(f"Unexpected error during handshake: {e}")
    finally:
        # Temizlik işlemleri - nickname None olabilir
        if nickname:
            chat_core.remove_client(nickname)
            chat_core.broadcast(f'{nickname} left the chat!')
            if nickname in last_pong:
                del last_pong[nickname]
            send_user_list()
        
        # Socket'i güvenli şekilde kapat
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            client_socket.close()
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f'Server started on {HOST}:{PORT}')
    threading.Thread(target=ping_clients, daemon=True).start()
    try:
        while True:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        print('Server shutting down.')
    finally:
        server.close()

if __name__ == '__main__':
    main()