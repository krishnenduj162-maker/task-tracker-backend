from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal
from models import Task, User
from schemas import TaskCreate, PriorityRequest

from dotenv import load_dotenv
#from openai import OpenAI
import os

app = FastAPI()
@app.get("/")
def home():
    return {"message": "Backend is running on Railway 🚀"}
load_dotenv()

#client = OpenAI(
 #   api_key=os.getenv("OPENAI_API_KEY")
#)

# ===================== MIDDLEWARE =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== REGISTER =====================
@app.post("/register")
def register(user: dict):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == user["username"]).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        username=user["username"],
        password=user["password"]
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}

# ===================== LOGIN =====================
@app.post("/login")
def login(user: dict):
    db = SessionLocal()

    db_user = db.query(User).filter(User.username == user["username"]).first()

    if not db_user or db_user.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "username": db_user.username
    }

# ===================== GET TASKS =====================
@app.get("/tasks")
def get_tasks():
    db = SessionLocal()

    tasks = db.query(Task).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "description": t.description,
            "due_date": t.due_date   # 👈 ADD THIS
        }
        for t in tasks
    ]

# ===================== CREATE TASK =====================
@app.post("/tasks")
def add_task(task: TaskCreate):
    db = SessionLocal()

    new_task = Task(
        title=task.title,
        status=task.status,
        priority=task.priority,
        description=task.description,
        due_date=task.due_date   # 👈 ADD THIS
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "id": new_task.id,
        "title": new_task.title,
        "status": new_task.status,
        "priority": new_task.priority,
        "description": new_task.description,
        "due_date": new_task.due_date   # 👈 ADD THIS TOO
    }
# ===================== UPDATE TASK =====================
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskCreate):
    db = SessionLocal()

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = updated_task.title
    task.status = updated_task.status
    task.priority = updated_task.priority
    task.description = updated_task.description

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "description": task.description
    }

# ===================== DELETE TASK =====================
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted"}

# ===================== AI PRIORITY =====================
@app.post("/ai-priority")
def ai_priority(data: PriorityRequest):

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f"""
You are an AI Task Manager.

Classify the following task into exactly one of these priorities:

High
Medium
Low

Also provide a one-line reason.

Task:
{data.task}

Respond strictly in this format:

Priority: <High/Medium/Low>
Reason: <one line>
"""
        )

        return {
            "result": response.output_text,
            "source": "OpenAI"
        }

    except Exception:

        task = data.task.lower()

        if any(word in task for word in [
            "today", "tomorrow", "urgent", "asap", "deadline",
            "exam", "report", "submission", "project", "interview"
        ]):
            priority = "High"
            reason = "The task has an immediate deadline or high importance."

        elif any(word in task for word in [
            "week", "meeting", "study", "assignment", "practice", "prepare"
        ]):
            priority = "Medium"
            reason = "The task is important but not immediately urgent."

        else:
            priority = "Low"
            reason = "The task appears routine and can be scheduled later."

        return {
            "result": f"Priority: {priority}\nReason: {reason}",
            "source": "Local AI Fallback"
        }