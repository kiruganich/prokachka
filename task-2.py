import socket

HOST = '0.0.0.0'
PORT = 8080

def handle_request(request_data: str):
    lines = request_data.split("\r\n")
    request_line = lines[0]

    try:
        path = request_line.split(" ")
    except ValueError:
        return "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"
    body = f"Path: {path}\n"

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n" +
        body
    )
    return response

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"Listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            with conn:
                print("Connected:", addr)
                request_bytes = conn.recv(4096)
                if not request_bytes:
                    continue

                request_text = request_bytes.decode("utf-8", errors="ignore")
                print("HTTP REQUEST")
                print(request_text)
                response = handle_request(request_text)
                conn.sendall(response.encode("utf-8"))


if __name__ == "__main__":
    run_server()
