from socket import *
from threading import Thread
import json
import cv2
from time import sleep

def stream_video(conn, video_files):
    # frame_counts = [0] * len(video_files)
    current_file_index = 0
    while current_file_index < len(video_files):
        cap = cv2.VideoCapture(video_files[current_file_index])
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        start_frame = (total_frames // 3)*current_file_index
        end_frame = (total_frames // 3) * (current_file_index+1)
        print("START_FRAME : ", start_frame, " END_FRAME : ", end_frame, " TOTAL_FRAMES : ", total_frames)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame_data = cv2.imencode('.jpg', frame)[1].tobytes()
            conn.sendall((str(len(frame_data))).encode().ljust(16) + frame_data)
            if  current_frame >= end_frame:
                current_file_index += 1
                break
        cap.release()

def handle_client(client_socket, name):
    global client_keys
    global videos
    json_dict = json.dumps(client_keys)
    broadcast(json_dict.encode())

    while True:
        msg = client_socket.recv(1024)
        try:
            if msg.decode() == "QUIT":
                client_sockets.remove(client_socket)
                del client_keys[name]
                break
            elif msg.decode() == "LIST":
                client_socket.sendall("ACK".encode())   #to stop recv_thread
                sleep(1)
                msg = f"{videos}".encode()
                client_socket.sendall(msg)
                video_name = client_socket.recv(1024).decode()
                print(f"STREAMING {video_name} FOR {name}.")
                try:
                    video_files = [f"videos/{video_name}_360p.mp4", f"videos/{video_name}_720p.mp4", f"videos/{video_name}_1440p.mp4"]
                    stream_video(client_socket, video_files)
                except Exception as e:
                    print(f"ERROR : {e}")
                client_socket.sendall("ACK".encode())
        except UnicodeDecodeError:
            print("SENDING ENCRYPTED MESSAGE.")
            broadcast(msg)

    json_dict = json.dumps(client_keys)
    broadcast(json_dict.encode())
    print(f"CONNECTION FROM {name} CLOSED.")
    client_socket.close()

def broadcast(msg):
    global client_sockets
    for client in client_sockets:
        client.sendall(msg)





client_sockets = []
client_keys = {}
videos = ["wildlife", "scenic_coast"]
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('localhost', 7777))
server_socket.listen(5)
print("SERVER LISTENING...")

while True:
    client_socket, client_address = server_socket.accept()
    client_sockets.append(client_socket)
    name = client_socket.recv(1024).decode()
    client_public_key = client_socket.recv(1024)
    if (client_public_key.decode() == "QUIT"):
        continue
    client_keys[name] = client_public_key.decode()
    print(f"CONNECTION FROM {name} ESTABLISHED.")
    client_thread = Thread(target=handle_client, args=(client_socket, name))
    client_thread.start()