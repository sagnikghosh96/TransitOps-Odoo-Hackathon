import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
MANAGE_ROLES = ["Fleet Manager"]


@router.get("/", response_model=List[schemas.MaintenanceOut])
def list_maintenance(
    status: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    q = db.query(models.MaintenanceLog)
    if status:
        q = q.filter(models.MaintenanceLog.status == status)
    if vehicle_id:
        q = q.filter(models.MaintenanceLog.vehicle_id == vehicle_id)
    return q.order_by(models.MaintenanceLog.id.desc()).all()


@router.post("/", response_model=schemas.MaintenanceOut)
def create_maintenance(
    payload: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.status == models.VehicleStatus.on_trip:
        raise HTTPException(status_code=400, detail="Cannot send an on-trip vehicle to maintenance")

    log = models.MaintenanceLog(
        vehicle_id=payload.vehicle_id,
        description=payload.description,
        cost=payload.cost,
        status=models.MaintenanceStatus.active,
    )
    db.add(log)

    # Rule: Creating an active maintenance record automatically changes vehicle status to In Shop
    vehicle.status = models.VehicleStatus.in_shop

    db.commit()
    db.refresh(log)
    return log


@router.post("/{log_id}/close", response_model=schemas.MaintenanceOut)
def close_maintenance(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    log = db.query(models.MaintenanceLog).filter(models.MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    if log.status == models.MaintenanceStatus.closed:
        raise HTTPException(status_code=400, detail="Maintenance record already closed")

    log.status = models.MaintenanceStatus.closed
    log.closed_at = datetime.datetime.utcnow()

    vehicle = log.vehicle
    # Rule: Closing maintenance restores vehicle to Available (unless retired)
    other_active = db.query(models.MaintenanceLog).filter(
        models.MaintenanceLog.vehicle_id == vehicle.id,
        models.MaintenanceLog.status == models.MaintenanceStatus.active,
        models.MaintenanceLog.id != log.id,
    ).first()
    if vehicle.status != models.VehicleStatus.retired and not other_active:
        vehicle.status = models.VehicleStatus.available

    db.commit()
    db.refresh(log)
    return log