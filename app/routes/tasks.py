from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.utils.email_utils import send_task_notification

router = APIRouter()


# Dependency to get database session

# Admin - Assign a task to a user
@router.post("/tasks")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Send email notification to assignee
    send_task_notification(task.assignee_email, f"Task: {task.title} has been assigned.")

    return db_task


# Admin - Update task status
@router.patch("/tasks/{task_id}")
def update_task_status(task_id: int, status: str, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.status = status
    db.commit()
    db.refresh(db_task)

    if status == "completed":
        # Notify admin when task is completed
        send_task_notification("admin_email@example.com", f"Task: {db_task.title} is completed by the user.")

    return db_task


# User - View tasks assigned to them
@router.get("/tasks")
def get_user_tasks(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.assignee_email == user_email).all()
    return tasks


# User - Upload file (<=1MB)
@router.post("/tasks/{task_id}/upload")
def upload_file(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Save file (optional: limit to 1MB)
    file_path = f"uploads/{task_id}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    db_task.file_path = file_path
    db.commit()
    db.refresh(db_task)
    return {"message": "File uploaded successfully"}


# User - Mark task as completed
@router.patch("/tasks/{task_id}/complete")
def mark_task_complete(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.status = "completed"
    db.commit()
    db.refresh(db_task)

    # Notify Admin about task completion
    send_task_notification("admin_email@example.com", f"Task: {db_task.title} completed by the user.")

    return db_task
