import os 
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import asdict
from dotenv import load_dotenv

from horoscope import star_news_agent, Inputs, PersonalizedNewspaper

import logfire
from markupsafe import escape
load_dotenv()  # Load .env variables
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))

app = FastAPI()
logfire.instrument_fastapi(app)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": "",
        "star_sign": "",
        "output": None,
        "error": None
    })

@app.post("/", response_class=HTMLResponse)
async def form_post(request: Request, name: str = Form(...), star_sign: str = Form(...)):
    valid_star_signs = {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    }

    name = escape(name.strip())
    star_sign = star_sign.strip().lower()

    if star_sign not in valid_star_signs:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "name": name,
            "star_sign": star_sign,
            "output": None,
            "error": "Invalid star sign. Please select a valid zodiac sign."
        })
    inputs = Inputs(name=name, star_sign=star_sign)

    result = await star_news_agent.run(str(inputs), deps=inputs)
    logfire.info(f"Star news agent {result}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": name,
        "star_sign": star_sign.lower(),
        "output": result.output,
        "error": None if result.output else "Failed to create personalized newspaper."
    })