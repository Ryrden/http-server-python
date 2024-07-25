import re
import socket


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, _ = server_socket.accept()

    data = client.recv(1024).decode()
    request, *_ = data.split("\r\n") 
    [_, path, _] = request.split(" ")

    echo_regex = re.compile(r"^/echo/(.*)$")
    if path == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif match := echo_regex.match(path):
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(match.group(1))}\r\n\r\n{match.group(1)}"
    elif path != "/":
        response = "HTTP/1.1 404 Not Found\r\n\r\n"

    client.send(response.encode())
    client.close()


if __name__ == "__main__":
    main()
