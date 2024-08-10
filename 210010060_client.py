from socket import *
from threading import Thread
from time import sleep
from time import time
import json
import cv2
import numpy as np
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

def receive_video(client_socket):
    while True:
        frame_size_data = client_socket.recv(16)
        if frame_size_data.decode() == "ACK":
            break
        frame_size = int(frame_size_data.strip())
        if frame_size == 0:
            break
        frame_data = b''
        while len(frame_data) < frame_size:
            remaining_bytes = frame_size - len(frame_data)
            frame_data += client_socket.recv(remaining_bytes)
        frame_np = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
        frame = cv2.resize(frame, (1080, 720))
        cv2.imshow('Video Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

def receive_messages(client_socket):
    global running
    global private_key
    global client_keys
    try:
        while running:
            msg = client_socket.recv(2048)
            try:
                if (msg.decode() == "ACK"):
                    running = False
                    break
                msg1 = msg.decode()
                msg2 = json.loads(msg1)
                print(f"AVAILABLE CLIENTS : ", end=" ")
                # client_keys = {}
                for key, value in msg2.items():
                    # processed_value = value.replace('\n', '')
                    client_keys[key] = value
                    print(key, end=" ")
                print("\n")
                continue
            except UnicodeDecodeError:
                print("RECIEVED ENCRYPTED MESSAGE.")

            try:
                cipher_rsa = PKCS1_OAEP.new(private_key)
                decrypted_data = cipher_rsa.decrypt(msg)
                print("PRIVATE MESSAGE : ", decrypted_data.decode())
            except:
                print("INCORRECT DECRYPTION, MESSAGE NOT FOR YOU.")
    except json.JSONDecodeError:
        pass            #nothing to see here
        
    

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(('localhost', 7777))
running = True
client_keys = {}

name = input("ENTER YOUR NAME : ")
client_socket.sendall(name.encode())
key = RSA.generate(1024)
private_key = key
public_key = key.publickey().export_key()
sleep(1)
print(public_key.decode())
ok = input("\nENTER OK TO SEND PUBLIC KEY : ")
if ok == "OK":
    client_socket.sendall(public_key)
else:
    client_socket.sendall("QUIT".encode())
    print("NO CHOICE BUT TO EXIT!")
    client_socket.close()
    exit(1)

recv_thread = Thread(target=receive_messages, args=(client_socket,))
recv_thread.start()

print(f"ENTER YOUR MESSAGE OR 'LIST' OR 'QUIT'")
while True:
    msg = input()
    if msg == "QUIT":
        client_socket.sendall(msg.encode())
        running = False
        print(f"EXITING...")
        break
    elif msg == "LIST":
        client_socket.sendall(msg.encode())
        recv_thread.join()          #wait for recv thread to end
        videos = client_socket.recv(1024).decode()
        print(videos)
        video_name = input("SELECT VIDEO : ")
        client_socket.sendall(video_name.encode())
        print("PLAYING VIDEO...")
        receive_video(client_socket)
        print("VIDEO ENDED.")
        running = True
        recv_thread = Thread(target=receive_messages, args=(client_socket,))
        recv_thread.start()
    else:
        recipient = input("ENTER RECIPIENT'S NAME : ")
        recipient_key = client_keys[recipient]
        recipient_key_obj = RSA.import_key(recipient_key)      
        cipher_rsa = PKCS1_OAEP.new(recipient_key_obj)
        encrypted_data = cipher_rsa.encrypt(msg.encode())
        client_socket.sendall(encrypted_data)

client_socket.close()