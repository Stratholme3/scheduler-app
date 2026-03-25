# Scheduler App (نظام جدولة الخدمات)

A duty scheduling system that distributes service assignments fairly among a group of people, with Arabic RTL interface.

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Vanilla HTML/CSS/JavaScript (RTL Arabic UI)
- **Templating**: Jinja2
- **Server**: Uvicorn on port 5000

## Running the App

The app runs via the "Start application" workflow:
```
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Project Structure

```
main.py              # FastAPI backend + scheduling algorithm
static/app.js        # Frontend JS (upload + generate)
templates/index.html # Main UI template
requirements.txt     # Python dependencies
```

## Features

- Upload a text file of names (one per line, at least 2 words each)
- Numbers in lines are stripped automatically
- Generates a duty schedule over N days
- Tracks workload per person to ensure fairness
- Enforces cooldown periods so the same person isn't assigned too frequently
- Platoon-based group duty (واجب فصيلة) assigned by rotating groups

## Services Configured

| Service    | Count/day | Weight | Cooldown |
|------------|-----------|--------|----------|
| اعاشة      | 12        | 5      | 3 days   |
| قيادة      | 2         | 1      | 0 days   |

## API Endpoints

- `GET /` — Serves the main UI
- `POST /upload` — Accepts a text file, populates the people list
- `GET /generate?days=N` — Generates and returns the schedule as JSON
