import traceback
import socket

MAX_CONCURRENT_REQUESTS = 10
HTTP_VERSION = "HTTP/1.1"
MAX_REQUEST_SIZE_BYTES = 10 * 1024
HTTP_STATUS_OK = 200


class Request:
    def __init__(
        self, method: str, path: str, query: dict[str, str], content_length: int, headers: dict[str, str], body: bytes
    ):
        self.method = method
        self.path = path
        self.query = query
        self.content_length = content_length
        self.headers = headers
        self.body = body

    def text(self) -> str:
        return self.body.decode()

    def json(self):
        import json

        return json.loads(self.text())

    def form_data(self):
        return Request._parse_query_str(self.text())

    # only supports ASCII, not UTF-8
    def _decode_uri_component(text: str) -> str:
        i = 0
        out = ""
        while i < len(text):
            if text[i] == "%":
                ascii_hex = text[i + 1 : i + 3]
                out += chr(int(ascii_hex, 16))
                i += 3
            else:
                out += text[i]
                i += 1

        return out

    def _parse_query_str(query_string: str) -> dict[str, str]:
        query = {}
        for arg in query_string.split("&"):
            if "=" not in arg:
                continue

            key, value = arg.split("=", maxsplit=1)
            query[key] = Request._decode_uri_component(value)

        return query

    def parse_header_from_bytes(data: str) -> "Request":
        lines = data.split("\r\n")

        method, full_path, _http_version = lines[0].split(" ")
        path_split = full_path.split("?", maxsplit=1)
        if len(path_split) == 2:
            path, query_string = path_split
        else:
            path, query_string = path_split[0], ""

        query = Request._parse_query_str(query_string)

        header_lines = lines[1:]
        headers = {}
        for line in header_lines:
            key, value = line.split(":", maxsplit=1)
            headers[key.strip().lower()] = value.strip()

        content_length = int(headers.get("content-length", 0))

        return Request(method.upper(), path, query, content_length, headers, bytes())


class Response:
    def __init__(self, status_code: int, body: bytes, headers: dict[str, str] = {}):
        self.status_code = status_code
        self.body = body
        self.headers = headers

    def from_python_obj(obj) -> "Response":
        if isinstance(obj, Response):
            return obj

        if isinstance(obj, dict):
            import json

            body = json.dumps(obj)
            return Response(HTTP_STATUS_OK, body.encode(), headers={"Content-Type": "application/json"})

        if isinstance(obj, str):
            return Response(HTTP_STATUS_OK, obj.encode(), headers={"Content-Type": "text/plain"})

        if isinstance(obj, tuple) and len(obj) == 2:
            if isinstance(obj[0], int):
                return Response(obj[0], obj[1].encode(), headers={"Content-Type": "text/plain"})
            else:
                return Response(HTTP_STATUS_OK, obj[1].encode(), headers={"Content-Type": obj[0]})

        raise RuntimeError("invalid response type returned by handler")

    def format(self, host: str) -> bytes:
        self.headers["Content-Length"] = str(len(self.body))
        self.headers["Host"] = host
        headers = [f"{key}: {value}\r\n" for (key, value) in self.headers.items()]
        return (f"{HTTP_VERSION} {self.status_code}\r\n" + "".join(headers) + "\r\n").encode() + self.body


class Server:
    def __init__(self, addr: str, port: int, debug: bool = False):
        self.addr = addr
        self.port = port
        self.debug = debug
        self.handlers = {}

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.addr, self.port))
        s.listen(MAX_CONCURRENT_REQUESTS)
        print(f"Listening on {self.addr}:{self.port}")

        self.main_loop(s)

    def main_loop(self, s: socket.socket):
        while True:
            (conn, _address) = s.accept()
            self.handle_request(conn)

    def handle_request(self, conn: socket.socket):
        try:
            request = self.read_request(conn)
            response = self.execute_handler(request)
        except Exception as e:
            if self.debug:
                print(traceback.format_exc())

            response = Response(500, str(e).encode())

        self.send_response(conn, response)

    def read_request(self, conn: socket.socket) -> Request:
        buf = bytes()

        def _read():
            nonlocal buf

            read = conn.recv(1024)
            if len(read) == 0:
                raise RuntimeError("failed to read request")

            buf += read
            if len(buf) >= MAX_REQUEST_SIZE_BYTES:
                raise RuntimeError("request too long")

        while len(buf) < MAX_REQUEST_SIZE_BYTES and b"\r\n\r\n" not in buf:
            _read()

        request_header, buf = buf.split(b"\r\n\r\n")
        request = Request.parse_header_from_bytes(request_header.decode())
        while len(buf) < min(request.content_length, MAX_REQUEST_SIZE_BYTES):
            _read()

        request.body = buf
        return request

    def send_response(self, conn: socket.socket, response: Response):
        message = response.format(self.addr)

        total_sent = 0
        while total_sent < len(message):
            total_sent += conn.send(message[total_sent:])
        conn.close()

    def route(self, path: str, methods: list[str] | None = None):
        def decorator(f):
            nonlocal path
            if not path.startswith("/"):
                path = f"/{path}"

            # lists can't be dict keys, so we have to join the methods
            methods_str = ",".join(methods) if methods else None
            self.handlers[(path, methods_str)] = f
            return f

        return decorator

    def get(self, path: str):
        return self.route(path, methods=["GET"])

    def post(self, path: str):
        return self.route(path, methods=["POST"])

    def execute_handler(self, request: Request) -> Response:
        for (path, methods), handler_fn in self.handlers.items():
            if request.path == path and (methods is None or request.method in methods):
                response_obj = handler_fn(request)
                return Response.from_python_obj(response_obj)

        return Response(404, b"Not found")
