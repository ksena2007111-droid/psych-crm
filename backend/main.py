from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from . import models
from .database import engine
from .routers import auth as auth_router
from .routers import clients as clients_router
from .routers import services as services_router
from .routers import sessions as sessions_router
from .routers import schedule as schedule_router
from .routers import bookings as bookings_router
from .routers import public as public_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRM для психолога")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

app.include_router(auth_router.router, prefix="/api")
app.include_router(clients_router.router, prefix="/api")
app.include_router(services_router.router, prefix="/api")
app.include_router(sessions_router.router, prefix="/api")
app.include_router(schedule_router.router, prefix="/api")
app.include_router(bookings_router.router, prefix="/api")
app.include_router(public_router.router, prefix="/api")


@app.get("/")
def root(request: Request):
    token = request.cookies.get("token")
    if token:
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@app.get("/clients")
def clients_page(request: Request):
    return templates.TemplateResponse(request, "clients.html")

@app.get("/clients/{client_id}")
def client_card_page(request: Request, client_id: int):
    return templates.TemplateResponse(request, "client_card.html", {"client_id": client_id})

@app.get("/calendar")
def calendar_page(request: Request):
    return templates.TemplateResponse(request, "calendar.html")

@app.get("/bookings")
def bookings_page(request: Request):
    return templates.TemplateResponse(request, "bookings.html")

@app.get("/services")
def services_page(request: Request):
    return templates.TemplateResponse(request, "services.html")

@app.get("/schedule")
def schedule_page(request: Request):
    return templates.TemplateResponse(request, "schedule.html")

@app.get("/logout")
def logout():
    response = RedirectResponse("/login")
    response.delete_cookie("token")
    return response