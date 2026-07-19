## Microhive

Minimal Python HTTP/1.1 server, built for MicroPython.

### Motivation
There are various HTTP servers with MicroPython compatibility, but they're often so complex that they can't be installed on an ESP8266 via MicroPython's package manager [`mip`](https://docs.micropython.org/en/latest/reference/packages.html) or are not very intuitive to use.

Microhive is aiming to provide a similar programming interface as FastAPI or Flask (but only provides a very small subset of their functionality).

### Usage
If you run it with MicroPython, first make sure to connect to a WiFi or start a hotspot on the MCU. If running on an ESP8266, you can follow up on the [official networking documentation](https://docs.micropython.org/en/latest/esp8266/quickref.html#networking).

```py
from microhive import Request, Response, Server

server = Server("0.0.0.0", 80)


@server.get("/")
def root(request: Request):
    return "server running"

@server.get("/hello")
def hello(request: Request):
    return Response(418, b"I'm a teapot")

@server.route("/method")
def method(request: Request):
    return {"method": request.method}


server.run()
```

You can now reach the website by opening the IP address of the MCU (can be obtained with `wlan.ipconfig("addr4")`) in your browser.

### Related Projects
- [micropyserver](https://github.com/troublegum/micropyserver)
- [microdot](https://github.com/miguelgrinberg/microdot)
