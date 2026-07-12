from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/expenses", tags=["Expenses"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
MANAGE_ROLES = ["Fleet Manager", "Financial Analyst"]


@router.get("/", response_model=List[schemas.ExpenseOut])
def list_expenses(
    vehicle_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    q = db.query(models.Expense)
    if vehicle_id:
        q = q.filter(models.Expense.vehicle_id == vehicle_id)
    if category:
        q = q.filter(models.Expense.category == category)
    return q.order_by(models.Expense.id.desc()).all()


@router.post("/", response_model=schemas.ExpenseOut)
def create_expense(
    payload: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    data = payload.model_dump(exclude_unset=True)
    expense = models.Expense(**data)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense