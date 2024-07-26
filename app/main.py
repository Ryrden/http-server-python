import re
import socket
import threading
import sys
import gzip

class HTTPRequest:
    def __init__(self, data: str) -> None:
        self.method: str = ""
        self.path: str = ""
        self.protocol: str = ""
        self.headers: dict[str, str] = {}
        self.body: str = ""
        self.parse(data)

    def parse(self, data: str) -> None:
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
    def __init__(self, status_code: int = 200, reason: str = "OK", headers: dict[str, str] = None, body: bytes = b"") -> None:
        self.status_code = status_code
        self.reason = reason
        self.headers = headers or {}
        self.body = body

    def build(self) -> bytes:
        response_line = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"
        headers = "\r\n".join(f"{key}: {value}" for key, value in self.headers.items())
        return response_line.encode() + headers.encode() + b"\r\n\r\n" + self.body

def handle_root() -> bytes:
    return HTTPResponse().build()

def handle_user_agent(request: HTTPRequest) -> bytes:
    user_agent = request.headers.get("User-Agent", "").encode()
    return HTTPResponse(
        headers={"Content-Type": "text/plain", "Content-Length": str(len(user_agent))},
        body=user_agent
    ).build()

def handle_echo(request: HTTPRequest) -> bytes:
    match = re.match(r"^/echo/(.+)$", request.path)
    if match:
        echo_message = match.group(1).strip()
        body = echo_message.encode()
        headers = {"Content-Type": "text/plain"}
        
        if "Accept-Encoding" in request.headers and "gzip" in request.headers["Accept-Encoding"]:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"
        
        headers["Content-Length"] = str(len(body))
        
        return HTTPResponse(headers=headers, body=body).build()
    return HTTPResponse(status_code=404, reason="Not Found").build()

def handle_file_get(_: HTTPRequest, file_name: str, directory: str) -> bytes:
    try:
        with open(f"{directory}/{file_name}", "rb") as file:
            file_content = file.read()
        return HTTPResponse(
            headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(file_content))},
            body=file_content
        ).build()
    except FileNotFoundError:
        return HTTPResponse(status_code=404, reason="Not Found").build()

def handle_file_post(request: HTTPRequest, file_name: str, directory: str) -> bytes:
    try:
        content_length = int(request.headers.get("Content-Length", 0))
        file_content = request.body[:content_length]
        with open(f"{directory}/{file_name}", "wb") as file:
            file.write(file_content.encode())
        return HTTPResponse(status_code=201, reason="Created").build()
    except Exception:
        return HTTPResponse(status_code=400, reason="Bad Request").build()

def handle_request(request_data: str) -> bytes:
    request = HTTPRequest(request_data)

    if request.method == "GET":
        if request.path == "/":
            return handle_root()
        if request.path == "/user-agent":
            return handle_user_agent(request)
        if re.match(r"^/echo/(.+)$", request.path):
            return handle_echo(request)
        if match := re.match(r"^/files/(.+)$", request.path):
            directory = sys.argv[2]
            return handle_file_get(request, match.group(1), directory)

    if request.method == "POST" and (match := re.match(r"^/files/(.+)$", request.path)):
        directory = sys.argv[2]
        return handle_file_post(request, match.group(1), directory)

    return HTTPResponse(status_code=404, reason="Not Found").build()

def client_handler(client: socket.socket) -> None:
    try:
        data = client.recv(1024).decode().strip()
        if data:
            response = handle_request(data)
            client.send(response)
    finally:
        client.close()

def main() -> None:
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()
    print("Server listening on port 4221")

    while True:
        client, _ = server_socket.accept()
        threading.Thread(target=client_handler, args=(client,)).start()

if __name__ == "__main__":
    main()
