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

PEOPLE_FILE   = "people_data.json"
SCHEDULE_FILE = "schedule_data.json"
STATE_FILE    = "app_state.json"

# ── Disk helpers ────────────────────────────────────────

def load_people_from_disk():
    if os.path.exists(PEOPLE_FILE):
        with open(PEOPLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_people_to_disk(data):
    with open(PEOPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_schedule_from_disk():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(k): v for k, v in raw.items()}
    return {}

def save_schedule_to_disk():
    data = {str(k): v for k, v in schedule.items()}
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_state_from_disk():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_state_to_disk():
    data = {
        "person_load":          {str(k): v for k, v in person_load.items()},
        "assignment_count":     {str(k): v for k, v in assignment_count.items()},
        "schedule_assigned_ids":{str(k): list(v) for k, v in schedule_assigned_ids.items()},
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

# ── Boot-time load ───────────────────────────────────────

people   = load_people_from_disk()
schedule = load_schedule_from_disk()
schedule_assigned_ids = {}
person_load     = defaultdict(int)
last_assigned   = defaultdict(lambda: -999)
last_service    = defaultdict(lambda: -999)
assignment_count = defaultdict(int)

_state = load_state_from_disk()
if _state:
    for k, v in _state["person_load"].items():
        person_load[int(k)] = v
    for k, v in _state["assignment_count"].items():
        assignment_count[int(k)] = v
    for k, v in _state["schedule_assigned_ids"].items():
        schedule_assigned_ids[int(k)] = set(v)

services = [
    {"name": "اعاشة",       "count": 12, "weight": 5, "cooldown": 3},
    {"name": "قيادة",       "count": 2,  "weight": 1, "cooldown": 0},
    {"name": "عيادة",       "count": 2,  "weight": 1, "cooldown": 0},
    {"name": "امن",         "count": 1,  "weight": 1, "cooldown": 0},
    {"name": "خدمات عامة", "count": 5,  "weight": 3, "cooldown": 0},
    {"name": "ضباط",        "count": 2,  "weight": 1, "cooldown": 0},
    {"name": "ماس جنود",   "count": 6,  "weight": 3, "cooldown": 0},
]

# ── Scheduling logic ─────────────────────────────────────

def score(p, d):
    return (d - last_assigned[p["id"]]) * 2 - person_load[p["id"]] * 3

def generate(days):
    global schedule, schedule_assigned_ids, person_load, last_assigned, last_service, assignment_count

    schedule              = {}
    schedule_assigned_ids = {}
    person_load      = defaultdict(int)
    last_assigned    = defaultdict(lambda: -999)
    last_service     = defaultdict(lambda: -999)
    assignment_count = defaultdict(int)

    for d in range(days):
        schedule[d]    = {}
        assigned_today = set()

        platoon_id = d % 10
        group = [p for p in people if p["platoon"] == platoon_id]

        schedule[d]["واجب فصيلة"] = [p["name"] for p in group]
        for p in group:
            person_load[p["id"]]  += 5
            last_assigned[p["id"]] = d
            last_service[(p["id"], "واجب فصيلة")] = d
            assigned_today.add(p["id"])
            assignment_count[p["id"]] += 1

        for s in services:
            candidates = [
                p for p in people
                if p["id"] not in assigned_today
                and d - last_service[(p["id"], s["name"])]        >= s["cooldown"]
                and d - last_service[(p["id"], "واجب فصيلة")] >= 1
            ]
            candidates.sort(key=lambda p: score(p, d), reverse=True)
            selected = candidates[:s["count"]]

            for p in selected:
                person_load[p["id"]]  += s["weight"]
                last_assigned[p["id"]] = d
                last_service[(p["id"], s["name"])] = d
                assigned_today.add(p["id"])
                assignment_count[p["id"]] += 1

            schedule[d][s["name"]] = [p["name"] for p in selected]

        schedule_assigned_ids[d] = set(assigned_today)

    save_schedule_to_disk()
    save_state_to_disk()
    return schedule

# ── API endpoints ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global people
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("utf-8-sig")

    lines = text.splitlines()
    names = []
    for line in lines:
        line = re.sub(r'\d+', '', line).strip()
        if len(line.split()) >= 2:
            names.append(line)

    if not names:
        return {"status": "error", "message": "لم يتم العثور على أسماء"}

    people = [
        {
            "id":       i,
            "name":     names[i],
            "battalion": 0,
            "company":  i // 95,
            "platoon":  i // 19,
        }
        for i in range(len(names))
    ]
    save_people_to_disk(people)
    return {"status": "ok", "count": len(people)}


@app.get("/generate")
def gen(days: int):
    if not people:
        return {"error": "لم يتم تحميل الأسماء"}
    if days <= 0:
        return {"error": "عدد الأيام غير صالح"}
    return generate(days)


@app.get("/current-schedule")
def current_schedule():
    if not schedule:
        return {}
    return {str(k): v for k, v in schedule.items()}


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
            "name":        p["name"],
            "company":     p["company"] + 1,
            "platoon":     (p["platoon"] % 5) + 1,
            "load":        person_load[p["id"]],
            "assignments": assignment_count[p["id"]],
        }
        for p in people
    ]
    result.sort(key=lambda x: x["load"], reverse=True)
    return result


@app.get("/platoons")
def get_platoons():
    if not people:
        return {"total": 0, "companies": []}

    companies = {}
    for p in people:
        cid = p["company"]
        pid = p["platoon"]
        companies.setdefault(cid, {}).setdefault(pid, []).append(p["name"])

    result = []
    for cid in sorted(companies.keys()):
        platoons_list = []
        for idx, pid in enumerate(sorted(companies[cid].keys())):
            members = companies[cid][pid]
            platoons_list.append({
                "platoon":        idx + 1,   # 1-5 per company
                "global_platoon": pid,        # kept for scheduling logic
                "count":          len(members),
                "members":        members,
            })
        result.append({
            "company":      cid + 1,
            "member_count": sum(pl["count"] for pl in platoons_list),
            "platoons":     platoons_list,
        })

    return {"total": len(people), "companies": result}


# ── Print / PDF endpoints ────────────────────────────────

def _print_css():
    return """
    <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; direction: rtl; color: #000;
           background: #fff; padding: 20px; font-size: 13px; }
    h1 { font-size: 18px; text-align: center; margin-bottom: 16px; }
    h2 { font-size: 15px; margin: 16px 0 8px; border-bottom: 2px solid #000;
         padding-bottom: 4px; }
    h3 { font-size: 13px; margin: 10px 0 4px; color: #333; }
    .names { line-height: 2; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { border: 1px solid #888; padding: 6px 10px; text-align: right; }
    th { background: #ddd; font-weight: bold; }
    .load-bar-wrap { background: #ddd; border-radius: 3px; height: 8px; }
    .load-bar { height: 8px; background: #2d8cff; border-radius: 3px; }
    @media print { button { display: none; } }
    .print-btn { display:block; margin:0 auto 16px; padding:10px 30px;
                 background:#2d8cff; color:#fff; border:none; border-radius:6px;
                 font-size:14px; cursor:pointer; }
    </style>
    """

@app.get("/print/schedule", response_class=HTMLResponse)
def print_schedule():
    if not schedule:
        return HTMLResponse("<p>لا يوجد جدول. قم بتوليد الجدول أولاً.</p>")

    html = f"<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'>{_print_css()}</head><body>"
    html += "<button class='print-btn' onclick='window.print()'>طباعة / حفظ PDF</button>"
    html += "<h1>جدول الخدمات</h1>"

    for d in sorted(schedule.keys()):
        html += f"<h2>اليوم {d + 1}</h2>"
        for service, names in schedule[d].items():
            html += f"<h3>{service} ({len(names)})</h3>"
            html += f"<p class='names'>{' &nbsp;·&nbsp; '.join(names)}</p>"

    html += "</body></html>"
    return HTMLResponse(html)


@app.get("/print/loads", response_class=HTMLResponse)
def print_loads():
    if not people:
        return HTMLResponse("<p>لا توجد بيانات.</p>")

    stats = [
        {
            "name":        p["name"],
            "company":     p["company"] + 1,
            "platoon":     (p["platoon"] % 5) + 1,
            "load":        person_load[p["id"]],
            "assignments": assignment_count[p["id"]],
        }
        for p in people
    ]
    stats.sort(key=lambda x: x["load"], reverse=True)
    max_load = max((s["load"] for s in stats), default=1) or 1

    html = f"<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'>{_print_css()}</head><body>"
    html += "<button class='print-btn' onclick='window.print()'>طباعة / حفظ PDF</button>"
    html += "<h1>توزيع الأحمال</h1>"
    html += """<table><thead><tr>
        <th>#</th><th>الاسم</th><th>السرية</th><th>الفصيلة</th>
        <th>المرات</th><th>الحمل</th>
    </tr></thead><tbody>"""

    for i, s in enumerate(stats, 1):
        pct = round(s["load"] / max_load * 100)
        bar = f"<div class='load-bar-wrap'><div class='load-bar' style='width:{pct}%'></div></div>"
        html += (
            f"<tr><td>{i}</td><td>{s['name']}</td>"
            f"<td>{s['company']}</td><td>{s['platoon']}</td>"
            f"<td>{s['assignments']}</td><td>{bar}</td></tr>"
        )

    html += "</tbody></table></body></html>"
    return HTMLResponse(html)
