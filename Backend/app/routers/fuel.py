from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/fuel-logs", tags=["Fuel"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
MANAGE_ROLES = ["Fleet Manager", "Driver"]


@router.get("/", response_model=List[schemas.FuelLogOut])
def list_fuel_logs(
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    q = db.query(models.FuelLog)
    if vehicle_id:
        q = q.filter(models.FuelLog.vehicle_id == vehicle_id)
    return q.order_by(models.FuelLog.id.desc()).all()


@router.post("/", response_model=schemas.FuelLogOut)
def create_fuel_log(
    payload: schemas.FuelLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    data = payload.model_dump(exclude_unset=True)
    log = models.FuelLog(**data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log