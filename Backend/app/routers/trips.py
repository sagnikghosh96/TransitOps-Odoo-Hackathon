import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/trips", tags=["Trips"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]
DISPATCH_ROLES = ["Fleet Manager", "Driver"]


@router.get("/", response_model=List[schemas.TripOut])
def list_trips(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    q = db.query(models.Trip)
    if status:
        q = q.filter(models.Trip.status == status)
    return q.order_by(models.Trip.id.desc()).all()


@router.post("/", response_model=schemas.TripOut)
def create_trip(
    payload: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*DISPATCH_ROLES)),
):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == payload.vehicle_id).first()
    driver = db.query(models.Driver).filter(models.Driver.id == payload.driver_id).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Rule: Retired or In Shop vehicles must never appear in dispatch selection
    if vehicle.status in (models.VehicleStatus.retired, models.VehicleStatus.in_shop):
        raise HTTPException(status_code=400, detail="Vehicle is retired or in shop and cannot be dispatched")

    # Rule: vehicle already On Trip cannot be assigned to another trip
    if vehicle.status == models.VehicleStatus.on_trip:
        raise HTTPException(status_code=400, detail="Vehicle is already on a trip")

    # Rule: drivers with expired license or Suspended status cannot be assigned
    if driver.status == models.DriverStatus.suspended:
        raise HTTPException(status_code=400, detail="Driver is suspended and cannot be assigned")
    if driver.license_expiry_date <= datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Driver's license has expired")

    # Rule: driver already On Trip cannot be assigned to another trip
    if driver.status == models.DriverStatus.on_trip:
        raise HTTPException(status_code=400, detail="Driver is already on a trip")

    # Rule: cargo weight must not exceed vehicle max load capacity
    if payload.cargo_weight > vehicle.max_load_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Cargo weight ({payload.cargo_weight}kg) exceeds vehicle max load capacity ({vehicle.max_load_capacity}kg)",
        )

    trip = models.Trip(
        source=payload.source,
        destination=payload.destination,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        cargo_weight=payload.cargo_weight,
        planned_distance=payload.planned_distance,
        revenue=payload.revenue,
        status=models.TripStatus.draft,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/dispatch", response_model=schemas.TripOut)
def dispatch_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*DISPATCH_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != models.TripStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft trips can be dispatched")

    vehicle = trip.vehicle
    driver = trip.driver

    if vehicle.status != models.VehicleStatus.available:
        raise HTTPException(status_code=400, detail="Vehicle is no longer available")
    if driver.status != models.DriverStatus.available:
        raise HTTPException(status_code=400, detail="Driver is no longer available")
    if driver.license_expiry_date <= datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Driver's license has expired")

    # Rule: Dispatching automatically changes vehicle & driver status to On Trip
    vehicle.status = models.VehicleStatus.on_trip
    driver.status = models.DriverStatus.on_trip
    trip.status = models.TripStatus.dispatched
    trip.dispatched_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/complete", response_model=schemas.TripOut)
def complete_trip(
    trip_id: int,
    payload: schemas.TripComplete,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*DISPATCH_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != models.TripStatus.dispatched:
        raise HTTPException(status_code=400, detail="Only dispatched trips can be completed")

    vehicle = trip.vehicle
    driver = trip.driver

    trip.actual_distance = payload.actual_distance
    trip.fuel_consumed = payload.fuel_consumed
    trip.status = models.TripStatus.completed
    trip.completed_at = datetime.datetime.utcnow()

    # Rule: Completing a trip automatically changes vehicle & driver status back to Available
    vehicle.odometer = (vehicle.odometer or 0) + payload.actual_distance
    vehicle.status = models.VehicleStatus.available
    driver.status = models.DriverStatus.available

    # Auto-log fuel consumption for reporting
    if payload.fuel_consumed and payload.fuel_consumed > 0:
        fuel_log = models.FuelLog(
            vehicle_id=vehicle.id,
            liters=payload.fuel_consumed,
            cost=0,
        )
        db.add(fuel_log)

    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/cancel", response_model=schemas.TripOut)
def cancel_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*DISPATCH_ROLES)),
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status not in (models.TripStatus.draft, models.TripStatus.dispatched):
        raise HTTPException(status_code=400, detail="Only draft or dispatched trips can be cancelled")

    # Rule: Cancelling a dispatched trip restores vehicle & driver to Available
    if trip.status == models.TripStatus.dispatched:
        trip.vehicle.status = models.VehicleStatus.available
        trip.driver.status = models.DriverStatus.available

    trip.status = models.TripStatus.cancelled
    db.commit()
    db.refresh(trip)
    return trip