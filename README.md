## Microhive

Minimal Python HTTP/1.1 server, built for MicroPython.

### Usage
```py
from microhive import Request, Response, Server

server = Server("localhost", 8080)


@server.get("/")
def root(request: Request):
    return "server running"

@server.get("/hello")
def hello(request: Request):
    return Response(418, "I'm a teapot")

@server.route("/method")
def method(request: Request):
    return {"method": request.method}


server.run()
```

### Related Projects
- [micropyserver](https://github.com/troublegum/micropyserver)
- [microdot](https://github.com/miguelgrinberg/microdot)
