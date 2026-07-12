import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/drivers", tags=["Drivers"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
MANAGE_ROLES = ["Fleet Manager", "Safety Officer"]


@router.get("/", response_model=List[schemas.DriverOut])
def list_drivers(
    status: Optional[str] = None,
    dispatch_pool_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    q = db.query(models.Driver)
    if status:
        q = q.filter(models.Driver.status == status)
    if dispatch_pool_only:
        now = datetime.datetime.utcnow()
        q = q.filter(
            models.Driver.status == models.DriverStatus.available,
            models.Driver.license_expiry_date > now,
        )
    return q.order_by(models.Driver.id).all()


@router.post("/", response_model=schemas.DriverOut)
def create_driver(
    payload: schemas.DriverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    existing = db.query(models.Driver).filter(
        models.Driver.license_number == payload.license_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="License number must be unique")
    driver = models.Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=schemas.DriverOut)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/{driver_id}", response_model=schemas.DriverOut)
def update_driver(
    driver_id: int,
    payload: schemas.DriverUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}")
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*MANAGE_ROLES)),
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.status == models.DriverStatus.on_trip:
        raise HTTPException(status_code=400, detail="Cannot delete a driver who is on trip")
    db.delete(driver)
    db.commit()
    return {"detail": "Driver deleted"}