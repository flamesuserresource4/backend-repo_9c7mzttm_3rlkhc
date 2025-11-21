"""
Database Schemas for Gender & Youth Department Platform

Each Pydantic model below maps to a MongoDB collection using the lowercase
name of the class. For example, Event -> "event" collection.

Collections:
- event: Upcoming events managed by the department
- course: Course information per semester
- timetable: Semester timetable entries (per day/time/venue)
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import date as DateType


class Semester(str, Enum):
    Fall = "Fall"
    Spring = "Spring"
    Summer = "Summer"


class DayOfWeek(str, Enum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"


class Event(BaseModel):
    """Events collection schema"""
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Details about the event")
    date: DateType = Field(..., description="Event date")
    time: Optional[str] = Field(None, description="Event time (e.g., 10:00 AM)")
    location: Optional[str] = Field(None, description="Event location")
    audience: Optional[str] = Field(None, description="Target audience (e.g., Students, Staff)")
    link: Optional[str] = Field(None, description="Optional registration/info link")


class Course(BaseModel):
    """Courses collection schema"""
    code: str = Field(..., description="Course code (e.g., GYD101)")
    title: str = Field(..., description="Course title")
    semester: Semester = Field(..., description="Semester offering")
    year: int = Field(..., ge=2000, le=2100, description="Academic year (e.g., 2025)")
    lecturer: Optional[str] = Field(None, description="Course lecturer/instructor")
    credits: Optional[int] = Field(3, ge=0, le=30, description="Credit units")
    description: Optional[str] = Field(None, description="Short course description")


class Timetable(BaseModel):
    """Timetable collection schema"""
    semester: Semester = Field(..., description="Semester")
    year: int = Field(..., ge=2000, le=2100, description="Academic year")
    day: DayOfWeek = Field(...)
    start_time: str = Field(..., description="Start time (e.g., 09:00)")
    end_time: str = Field(..., description="End time (e.g., 10:30)")
    course_code: str = Field(..., description="Course code this slot belongs to")
    venue: Optional[str] = Field(None, description="Classroom or hall")
    lecturer: Optional[str] = Field(None, description="Lecturer name")
    notes: Optional[str] = Field(None, description="Additional information")
