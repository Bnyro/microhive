from microhive import Request, Response, Server

server = Server("0.0.0.0", 8080, debug=True)


@server.get("/")
def root(_request: Request):
    return "server running"


@server.get("/hello")
def hello(_request: Request):
    return Response(418, b"I'm a teapot")


@server.route("/method")
def method(request: Request):
    return {"method": request.method}


server.run()
