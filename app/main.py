from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request : Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/weather")
async def weather(request : Request, city: str = Form(...), unit: str = Form(...)):
    return templates.TemplateResponse(request=request, name="index.html", context={"city": city, "unit": unit})