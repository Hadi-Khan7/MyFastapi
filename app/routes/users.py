from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.utils.email_utils import send_task_notification

router = APIRouter()


# User - Get tasks assigned to them

@router.get("/tasks")
def get_user_tasks(db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.assignee_email == user_email).all()
    return tasks


# User - Upload file as part of a task
@router.post("/tasks/{task_id}/upload")
def upload_file(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Save file (assuming 1MB file size limit)
    if file.size > 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the limit of 1MB")

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

    # Notify admin about task completion
    send_task_notification("admin_email@example.com", f"Task '{db_task.title}' completed by user.")

    return db_task
