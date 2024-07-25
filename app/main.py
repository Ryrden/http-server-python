import re
import socket
import threading
import sys

class HTTPRequest:
    def __init__(self, data):
        self.method, self.path, self.protocol = None, None, None
        self.headers, self.body = {}, ""
        self.parse(data)

    def parse(self, data):
        lines = data.split("\r\n")
        self.method, self.path, self.protocol = lines[0].split(" ")
        header_lines = lines[1:]

        body_started = False
        for line in header_lines:
            if body_started:
                self.body += line
            elif line == "":
                body_started = True
            elif ": " in line:
                key, value = line.split(": ", 1)
                self.headers[key] = value

class HTTPResponse:
    def __init__(self, status_code=200, reason="OK", headers=None, body=""):
        if headers is None:
            headers = {}
        self.status_code = status_code
        self.reason = reason
        self.headers = headers
        self.body = body

    def build(self):
        response_line = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
        headers = "\r\n".join([f"{key}: {value}" for key, value in self.headers.items()])
        return f"{response_line}{headers}\r\n\r\n{self.body}"

def handle_request(request_data):
    request = HTTPRequest(request_data)

    if request.method == "GET" and request.path == "/":
        return HTTPResponse().build()

    if request.method == "GET" and request.path == "/user-agent":
        user_agent = request.headers.get("User-Agent", "")
        return HTTPResponse(
            headers={"Content-Type": "text/plain", "Content-Length": str(len(user_agent))},
            body=user_agent
        ).build()

    if request.method == "GET" and (match := re.match(r"^/echo/(.+)$", request.path)):
        echo_message = match.group(1)
        return HTTPResponse(
            headers={"Content-Type": "text/plain", "Content-Length": str(len(echo_message))},
            body=echo_message
        ).build()

    if match := re.match(r"^/files/(.+)$", request.path):
        directory = sys.argv[2]
        file_name = match.group(1)

        if request.method == "GET":
            try:
                with open(f"{directory}/{file_name}", "r") as file:
                    file_content = file.read()
                    return HTTPResponse(
                        headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(file_content))},
                        body=file_content
                    ).build()
            except Exception:
                return HTTPResponse(status_code=404, reason="Not Found").build()
        
        if request.method == "POST":
            try:
                content_length = int(request.headers.get("Content-Length", 0))
                file_content = request.body[:content_length]
                with open(f"{directory}/{file_name}", "w") as file:
                    file.write(file_content)
                return HTTPResponse(status_code=201, reason="Created").build()
            except Exception:
                return HTTPResponse(status_code=400, reason="Bad Request").build()

    return HTTPResponse(status_code=404, reason="Not Found").build()

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
