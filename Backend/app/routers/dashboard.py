from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]


@router.get("/kpis", response_model=schemas.DashboardKPIs)
def get_kpis(
    type: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    vq = db.query(models.Vehicle)
    if type:
        vq = vq.filter(models.Vehicle.type == type)
    if region:
        vq = vq.filter(models.Vehicle.region == region)
    vehicles = vq.all()

    total_vehicles = len(vehicles)
    active_vehicles = len([v for v in vehicles if v.status != models.VehicleStatus.retired])
    available_vehicles = len([v for v in vehicles if v.status == models.VehicleStatus.available])
    vehicles_in_maintenance = len([v for v in vehicles if v.status == models.VehicleStatus.in_shop])
    on_trip_vehicles = len([v for v in vehicles if v.status == models.VehicleStatus.on_trip])

    active_trips = db.query(models.Trip).filter(models.Trip.status == models.TripStatus.dispatched).count()
    pending_trips = db.query(models.Trip).filter(models.Trip.status == models.TripStatus.draft).count()
    drivers_on_duty = db.query(models.Driver).filter(models.Driver.status == models.DriverStatus.on_trip).count()

    fleet_utilization_pct = (on_trip_vehicles / active_vehicles * 100) if active_vehicles else 0.0

    return schemas.DashboardKPIs(
        active_vehicles=active_vehicles,
        available_vehicles=available_vehicles,
        vehicles_in_maintenance=vehicles_in_maintenance,
        active_trips=active_trips,
        pending_trips=pending_trips,
        drivers_on_duty=drivers_on_duty,
        fleet_utilization_pct=round(fleet_utilization_pct, 2),
    )