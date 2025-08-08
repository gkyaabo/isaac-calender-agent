# Isaac's Google Calendar Bridge (Railway-ready)
# Lightweight FastAPI app to receive schedule changes and write to Google Calendar

from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import os
import json
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials from environment variable or file
SERVICE_ACCOUNT_INFO = json.loads(os.environ.get("GOOGLE_CREDS_JSON"))
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Set up Google Calendar service
credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
calendar_service = build("calendar", "v3", credentials=credentials)

# Default calendar
CALENDAR_ID = "primary"
TIMEZONE = "Europe/London"  # Adjust if needed

# FastAPI app
app = FastAPI()

# Task schema
class CalendarTask(BaseModel):
    summary: str
    day: str  # e.g. "2025-08-08"
    start_time: str  # e.g. "14:00"
    end_time: str    # e.g. "16:00"
    description: Optional[str] = None

# Helper to format datetime string
def to_rfc3339(date_str: str, time_str: str) -> str:
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local = pytz.timezone(TIMEZONE).localize(dt)
    return local.isoformat()

@app.post("/add-task")
def add_task(task: CalendarTask):
    event = {
        "summary": task.summary,
        "start": {"dateTime": to_rfc3339(task.day, task.start_time), "timeZone": TIMEZONE},
        "end": {"dateTime": to_rfc3339(task.day, task.end_time), "timeZone": TIMEZONE},
    }
    if task.description:
        event["description"] = task.description

    created_event = calendar_service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {"status": "created", "eventId": created_event["id"]}

@app.get("/")
def root():
    return {"message": "Calendar Agent is live."}
