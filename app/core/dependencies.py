
from fastapi import Request,WebSocket
from app.container import ServiceContainer

def get_services(request: Request):
    return getattr(request.app.state, "services", None)

def get_services_ws(ws: WebSocket):
    return getattr(ws.app.state, "services", None)

