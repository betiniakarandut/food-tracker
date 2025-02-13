from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routes import meals
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Food Tracker API", description="API for tracking meal servings", version="1.0")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://your-render-app-name.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(meals.router, prefix="/meals", tags=["meals"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
