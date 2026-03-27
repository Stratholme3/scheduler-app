from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from collections import defaultdict
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

people = []

services = [
    {"name": "اعاشة", "count": 12, "weight": 5, "cooldown": 3},
    {"name": "قيادة", "count": 2, "weight": 1, "cooldown": 0},
    {"name": "عيادة", "count": 2, "weight": 1, "cooldown": 0},
    {"name": "امن", "count": 1, "weight": 1, "cooldown": 0},
    {"name": "خدمات عامة", "count": 5, "weight": 3, "cooldown": 0},
    {"name": "ضباط", "count": 2, "weight": 1, "cooldown": 0},
    {"name": "ماس جنود", "count": 6, "weight": 3, "cooldown": 0},
]

schedule = {}
person_load = defaultdict(int)
last_assigned = defaultdict(lambda: -999)
last_service = defaultdict(lambda: -999)

def score(p, d):
    return (d - last_assigned[p["id"]]) * 2 - person_load[p["id"]] * 3

def generate(days):
    global schedule, person_load, last_assigned, last_service

    schedule = {}
    person_load = defaultdict(int)
    last_assigned = defaultdict(lambda: -999)
    last_service = defaultdict(lambda: -999)

    for d in range(days):
        schedule[d] = {}
        assigned_today = set()

        # واجب فصيلة
        platoon_id = d % 10
        group = [p for p in people if p["platoon"] == platoon_id]

        schedule[d]["واجب فصيلة"] = [p["name"] for p in group]

        for p in group:
            person_load[p["id"]] += 5
            last_assigned[p["id"]] = d
            last_service[(p["id"], "واجب فصيلة")] = d
            assigned_today.add(p["id"])

        # services
        for s in services:
            candidates = [
                p for p in people
                if p["id"] not in assigned_today
                and d - last_service[(p["id"], s["name"])] >= s["cooldown"]
            ]

            candidates.sort(key=lambda p: score(p, d), reverse=True)
            selected = candidates[:s["count"]]

            for p in selected:
                person_load[p["id"]] += s["weight"]
                last_assigned[p["id"]] = d
                last_service[(p["id"], s["name"])] = d
                assigned_today.add(p["id"])

            schedule[d][s["name"]] = [p["name"] for p in selected]

    return schedule

# -------- Suggest replacements --------
@app.get("/suggest")
def suggest(day: int, service: str, name: str):
    if day not in schedule:
        return []

    # find person
    target = next((p for p in people if p["name"] == name), None)
    if not target:
        return []

    # people already assigned that day
    assigned = set()
    for s in schedule[day]:
        for n in schedule[day][s]:
            assigned.add(n)

    candidates = [
        p for p in people
        if p["name"] not in assigned
    ]

    # smart sort
    candidates.sort(key=lambda p: (
        p["platoon"] != target["platoon"],  # prefer same platoon
        person_load[p["id"]]
    ))

    return [p["name"] for p in candidates[:10]]

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

    people = []
    for i in range(len(names)):
        people.append({
            "id": i,
            "name": names[i],
            "battalion": 0,
            "company": i // 95,
            "platoon": i // 19
        })

    return {"status": "ok", "count": len(people)}

@app.get("/generate")
def gen(days: int):
    return generate(days)
