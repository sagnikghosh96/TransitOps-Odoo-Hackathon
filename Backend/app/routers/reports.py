import csv
import io
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])

ALL_ROLES = ["Fleet Manager", "Driver", "Safety Officer", "Financial Analyst"]


def _build_vehicle_reports(db: Session) -> List[schemas.VehicleReport]:
    vehicles = db.query(models.Vehicle).all()
    reports = []
    for v in vehicles:
        total_distance = sum(
            (t.actual_distance or 0) for t in v.trips if t.status == models.TripStatus.completed
        )
        total_fuel = sum(f.liters for f in v.fuel_logs)
        fuel_cost = sum(f.cost for f in v.fuel_logs)
        maintenance_cost = sum(m.cost for m in v.maintenance_logs)
        other_expenses = sum(e.amount for e in v.expenses)
        revenue = sum(
            (t.revenue or 0) for t in v.trips if t.status == models.TripStatus.completed
        )

        operational_cost = fuel_cost + maintenance_cost + other_expenses
        fuel_efficiency = (total_distance / total_fuel) if total_fuel else 0.0
        roi = (
            (revenue - (maintenance_cost + fuel_cost)) / v.acquisition_cost
            if v.acquisition_cost
            else 0.0
        )

        reports.append(
            schemas.VehicleReport(
                vehicle_id=v.id,
                registration_number=v.registration_number,
                fuel_efficiency=round(fuel_efficiency, 3),
                total_distance=round(total_distance, 2),
                total_fuel=round(total_fuel, 2),
                operational_cost=round(operational_cost, 2),
                revenue=round(revenue, 2),
                roi=round(roi, 4),
            )
        )
    return reports


@router.get("/vehicles", response_model=List[schemas.VehicleReport])
def vehicle_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    return _build_vehicle_reports(db)


@router.get("/vehicles/export.csv")
def export_vehicle_reports_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(*ALL_ROLES)),
):
    reports = _build_vehicle_reports(db)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Vehicle ID", "Registration Number", "Fuel Efficiency (km/l)",
        "Total Distance (km)", "Total Fuel (l)", "Operational Cost",
        "Revenue", "ROI",
    ])
    for r in reports:
        writer.writerow([
            r.vehicle_id, r.registration_number, r.fuel_efficiency,
            r.total_distance, r.total_fuel, r.operational_cost,
            r.revenue, r.roi,
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vehicle_reports.csv"},
    )