## Microhive

Minimal Python HTTP/1.1 server, built for MicroPython.

### Motivation
There are various HTTP servers with MicroPython compatibility, but they're often so complex that they can't be installed on an ESP8266 via MicroPython's package manager [`mip`](https://docs.micropython.org/en/latest/reference/packages.html) or are not very intuitive to use.

Microhive is aiming to provide a similar programming interface as FastAPI or Flask (but only provides a very small subset of their functionality).

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
