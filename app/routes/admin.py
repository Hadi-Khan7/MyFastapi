from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.utils.email_utils import send_task_notification
from app.auth import get_current_user

router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return {"message": "Welcome to Admin Dashboard"}
# Dependency to get current admin (similar to the previous auth function)
def get_current_admin(db: Session = Depends(get_db)):
    # Assuming an authorization function to get admin info from JWT token
    pass  # Implement logic for extracting admin info from JWT


# Admin - Assign new task to a user
@router.post("/tasks")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Send email notification to assignee
    send_task_notification(task.assignee_email, f"New Task: {task.title} assigned to you")

    return db_task


# Admin - View all tasks (all users' tasks)
@router.get("/tasks")
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    return tasks


# Admin - Update task status (pending/completed)
@router.patch("/tasks/{task_id}")
def update_task_status(task_id: int, status: str, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.status = status
    db.commit()
    db.refresh(db_task)

    if status == "completed":
        # Send completion notification to the admin
        send_task_notification("admin_email@example.com", f"Task '{db_task.title}' completed.")

    return db_task
