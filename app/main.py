import re
import socket
import threading

def handle_request(data):
    request = data.split("\r\n")
    path = request[0].split(" ")[1]
    
    if path == "/":
        return "HTTP/1.1 200 OK\r\n\r\n"
    
    if path == "/user-agent":
        user_agent = request[2].split(":")[1].strip()
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
    
    if path.startswith("/echo/"):
        match = re.match(r"^/echo/(.*)$", path)
        if match:
            echo_message = match.group(1)
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo_message)}\r\n\r\n{echo_message}"
    
    return "HTTP/1.1 404 Not Found\r\n\r\n"

def client_handler(client):
    try:
        data = client.recv(1024).decode().strip()
        if data:
            response = handle_request(data)
            client.send(response.encode())
    finally:
        client.close()

def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()
    
    while True:
        client, _ = server_socket.accept()
        threading.Thread(target=client_handler, args=(client,)).start()

if __name__ == "__main__":
    main()
