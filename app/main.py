from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth, users, admin, tasks
from app.database import Base, engine


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="a1b2c3dsadklaqwqd4e5f6")


# Create database tables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.routes import auth, users, admin, tasks
from app.database import Base, engine

app = FastAPI()

# Add session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key="a1b2c3dsadklaqwqd4e5f6")

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(tasks.router)

# Root → redirect to login page (let auth router handle the login page)
@app.get("/")
def root():
    return RedirectResponse(url="/login")
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
