from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from collections import defaultdict
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------- Data --------
people = []
services = [
    {"name": "اعاشة", "count": 12, "weight": 5, "cooldown": 3},
    {"name": "قيادة", "count": 2, "weight": 1, "cooldown": 0},
]

schedule = {}

# -------- Core --------
def generate(days):
    global schedule
    schedule = {}

    person_load = defaultdict(int)
    last_assigned = defaultdict(lambda: -999)
    last_service = defaultdict(lambda: -999)

    for d in range(days):
        schedule[d] = {}

        group = [p for p in people if p["platoon"] == d % 10]

        for p in group:
            person_load[p["id"]] += 5
            last_assigned[p["id"]] = d

        schedule[d]["واجب فصيلة"] = [p["name"] for p in group]

        for s in services:
            cand = [
                p for p in people
                if last_assigned[p["id"]] != d
                and d - last_service[(p["id"], s["name"])] >= s["cooldown"]
            ]

            cand.sort(key=lambda p: person_load[p["id"]])
            sel = cand[:s["count"]]

            for p in sel:
                person_load[p["id"]] += s["weight"]
                last_assigned[p["id"]] = d
                last_service[(p["id"], s["name"])] = d

            schedule[d][s["name"]] = [p["name"] for p in sel]

    return schedule

# -------- Routes --------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global people
    content = await file.read()
    lines = content.decode("utf-8").splitlines()

    names = []
    for line in lines:
        line = re.sub(r'\d+', '', line).strip()
        if len(line.split()) >= 2:
            names.append(line)

    people = [
        {"id": i, "name": names[i] if i < len(names) else f"شخص {i}", "platoon": i // 19}
        for i in range(190)
    ]

    return {"status": "ok"}

@app.get("/generate")
def gen(days: int):
    return generate(days)
