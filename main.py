from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from collections import defaultdict
import re
import json
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PEOPLE_FILE = "people_data.json"

def load_people_from_disk():
    if os.path.exists(PEOPLE_FILE):
        with open(PEOPLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_people_to_disk(data):
    with open(PEOPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

people = load_people_from_disk()

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
schedule_assigned_ids = {}  # day -> set of person IDs assigned that day
person_load = defaultdict(int)
last_assigned = defaultdict(lambda: -999)
last_service = defaultdict(lambda: -999)
assignment_count = defaultdict(int)

def score(p, d):
    return (d - last_assigned[p["id"]]) * 2 - person_load[p["id"]] * 3

def generate(days):
    global schedule, schedule_assigned_ids, person_load, last_assigned, last_service, assignment_count

    schedule = {}
    schedule_assigned_ids = {}
    person_load = defaultdict(int)
    last_assigned = defaultdict(lambda: -999)
    last_service = defaultdict(lambda: -999)
    assignment_count = defaultdict(int)

    for d in range(days):
        schedule[d] = {}
        assigned_today = set()

        platoon_id = d % 10
        group = [p for p in people if p["platoon"] == platoon_id]

        schedule[d]["واجب فصيلة"] = [p["name"] for p in group]

        for p in group:
            person_load[p["id"]] += 5
            last_assigned[p["id"]] = d
            last_service[(p["id"], "واجب فصيلة")] = d
            assigned_today.add(p["id"])
            assignment_count[p["id"]] += 1

        for s in services:
            candidates = [
                p for p in people
                if p["id"] not in assigned_today
                and d - last_service[(p["id"], s["name"])] >= s["cooldown"]
                and d - last_service[(p["id"], "واجب فصيلة")] >= 1
            ]

            candidates.sort(key=lambda p: score(p, d), reverse=True)
            selected = candidates[:s["count"]]

            for p in selected:
                person_load[p["id"]] += s["weight"]
                last_assigned[p["id"]] = d
                last_service[(p["id"], s["name"])] = d
                assigned_today.add(p["id"])
                assignment_count[p["id"]] += 1

            schedule[d][s["name"]] = [p["name"] for p in selected]

        schedule_assigned_ids[d] = set(assigned_today)

    return schedule


@app.get("/suggest")
def suggest(day: int, service: str, name: str):
    if day not in schedule:
        return []

    target = next((p for p in people if p["name"] == name), None)
    if not target:
        return []

    assigned_ids = schedule_assigned_ids.get(day, set())

    candidates = [p for p in people if p["id"] not in assigned_ids]

    candidates.sort(key=lambda p: (
        p["platoon"] != target["platoon"],
        person_load[p["id"]]
    ))

    return [p["name"] for p in candidates[:10]]


@app.get("/stats")
def get_stats():
    if not people:
        return []
    result = [
        {
            "name": p["name"],
            "platoon": p["platoon"] + 1,
            "load": person_load[p["id"]],
            "assignments": assignment_count[p["id"]]
        }
        for p in people
    ]
    result.sort(key=lambda x: x["load"], reverse=True)
    return result


@app.get("/platoons")
def get_platoons():
    if not people:
        return []
    platoon_map = defaultdict(list)
    for p in people:
        platoon_map[p["platoon"]].append(p["name"])
    return [
        {"platoon": k + 1, "count": len(v), "members": v}
        for k, v in sorted(platoon_map.items())
    ]


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


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

    if not names:
        return {"status": "error", "message": "لم يتم العثور على أسماء"}

    people = []
    for i in range(len(names)):
        people.append({
            "id": i,
            "name": names[i],
            "battalion": 0,
            "company": i // 95,
            "platoon": i // 19
        })

    save_people_to_disk(people)
    return {"status": "ok", "count": len(people)}


@app.get("/generate")
def gen(days: int):
    if not people:
        return {"error": "لم يتم تحميل الأسماء"}
    if days <= 0:
        return {"error": "عدد الأيام غير صالح"}
    return generate(days)
