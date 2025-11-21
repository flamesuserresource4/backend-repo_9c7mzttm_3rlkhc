import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Event as EventSchema, Course as CourseSchema, Timetable as TimetableSchema

app = FastAPI(title="Gender & Youth Department API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Helpers
# --------------------------

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert datetime to isoformat for JSON
    for k, v in list(doc.items()):
        try:
            if hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        except Exception:
            pass
    return doc


def ensure_db_available():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available. Configure DATABASE_URL and DATABASE_NAME.")


# --------------------------
# Root & Health
# --------------------------
@app.get("/")
def read_root():
    return {"message": "Gender & Youth Department API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        ensure_db_available()
        response["connection_status"] = "Connected"
        response["database"] = "✅ Connected & Working"
        response["collections"] = db.list_collection_names()
    except HTTPException as e:
        response["database"] = f"❌ {e.detail}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# --------------------------
# Schema endpoint for viewer
# --------------------------
@app.get("/schema")
def get_schema():
    return {
        "event": EventSchema.model_json_schema(),
        "course": CourseSchema.model_json_schema(),
        "timetable": TimetableSchema.model_json_schema(),
    }


# --------------------------
# Models for updates (partial)
# --------------------------
class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    link: Optional[str] = None


class CourseUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None
    lecturer: Optional[str] = None
    credits: Optional[int] = None
    description: Optional[str] = None


class TimetableUpdate(BaseModel):
    semester: Optional[str] = None
    year: Optional[int] = None
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    course_code: Optional[str] = None
    venue: Optional[str] = None
    lecturer: Optional[str] = None
    notes: Optional[str] = None


# --------------------------
# Events
# --------------------------
@app.get("/api/events")
def list_events(limit: Optional[int] = None):
    ensure_db_available()
    docs = get_documents("event", {}, limit)
    return [serialize_doc(d) for d in docs]


@app.post("/api/events")
def create_event(payload: EventSchema):
    ensure_db_available()
    new_id = create_document("event", payload)
    doc = db["event"].find_one({"_id": ObjectId(new_id)})
    return serialize_doc(doc)


@app.put("/api/events/{event_id}")
def update_event(event_id: str, payload: EventUpdate):
    ensure_db_available()
    try:
        oid = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = db.command("isMaster").get("localTime")  # server time
    res = db["event"].update_one({"_id": oid}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    doc = db["event"].find_one({"_id": oid})
    return serialize_doc(doc)


@app.delete("/api/events/{event_id}")
def delete_event(event_id: str):
    ensure_db_available()
    try:
        oid = ObjectId(event_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")
    res = db["event"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True}


# --------------------------
# Courses
# --------------------------
@app.get("/api/courses")
def list_courses(semester: Optional[str] = None, year: Optional[int] = None, limit: Optional[int] = None):
    ensure_db_available()
    query: Dict[str, Any] = {}
    if semester:
        query["semester"] = semester
    if year is not None:
        query["year"] = year
    docs = get_documents("course", query, limit)
    return [serialize_doc(d) for d in docs]


@app.post("/api/courses")
def create_course(payload: CourseSchema):
    ensure_db_available()
    new_id = create_document("course", payload)
    doc = db["course"].find_one({"_id": ObjectId(new_id)})
    return serialize_doc(doc)


@app.put("/api/courses/{course_id}")
def update_course(course_id: str, payload: CourseUpdate):
    ensure_db_available()
    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course id")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = db.command("isMaster").get("localTime")
    res = db["course"].update_one({"_id": oid}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    doc = db["course"].find_one({"_id": oid})
    return serialize_doc(doc)


@app.delete("/api/courses/{course_id}")
def delete_course(course_id: str):
    ensure_db_available()
    try:
        oid = ObjectId(course_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid course id")
    res = db["course"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"success": True}


# --------------------------
# Timetable
# --------------------------
@app.get("/api/timetable")
def list_timetable(semester: Optional[str] = None, year: Optional[int] = None, day: Optional[str] = None, limit: Optional[int] = None):
    ensure_db_available()
    query: Dict[str, Any] = {}
    if semester:
        query["semester"] = semester
    if year is not None:
        query["year"] = year
    if day:
        query["day"] = day
    docs = get_documents("timetable", query, limit)
    # Sort by day then start_time for better readability if not filtered
    results = [serialize_doc(d) for d in docs]
    return results


@app.post("/api/timetable")
def create_timetable(payload: TimetableSchema):
    ensure_db_available()
    new_id = create_document("timetable", payload)
    doc = db["timetable"].find_one({"_id": ObjectId(new_id)})
    return serialize_doc(doc)


@app.put("/api/timetable/{slot_id}")
def update_timetable(slot_id: str, payload: TimetableUpdate):
    ensure_db_available()
    try:
        oid = ObjectId(slot_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timetable id")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = db.command("isMaster").get("localTime")
    res = db["timetable"].update_one({"_id": oid}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Timetable slot not found")
    doc = db["timetable"].find_one({"_id": oid})
    return serialize_doc(doc)


@app.delete("/api/timetable/{slot_id}")
def delete_timetable(slot_id: str):
    ensure_db_available()
    try:
        oid = ObjectId(slot_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timetable id")
    res = db["timetable"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Timetable slot not found")
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
