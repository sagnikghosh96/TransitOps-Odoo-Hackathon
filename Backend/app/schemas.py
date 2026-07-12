import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from .models import RoleEnum, VehicleStatus, DriverStatus, TripStatus, MaintenanceStatus


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Vehicle ----------
class VehicleBase(BaseModel):
    registration_number: str
    name_model: str
    type: str
    max_load_capacity: float
    odometer: float = 0
    acquisition_cost: float = 0
    region: str = "Unassigned"


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name_model: Optional[str] = None
    type: Optional[str] = None
    max_load_capacity: Optional[float] = None
    odometer: Optional[float] = None
    acquisition_cost: Optional[float] = None
    region: Optional[str] = None
    status: Optional[VehicleStatus] = None


class VehicleOut(VehicleBase):
    id: int
    status: VehicleStatus

    class Config:
        from_attributes = True


# ---------- Driver ----------
class DriverBase(BaseModel):
    name: str
    license_number: str
    license_category: str
    license_expiry_date: datetime.datetime
    contact_number: str
    safety_score: float = 100


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    license_category: Optional[str] = None
    license_expiry_date: Optional[datetime.datetime] = None
    contact_number: Optional[str] = None
    safety_score: Optional[float] = None
    status: Optional[DriverStatus] = None


class DriverOut(DriverBase):
    id: int
    status: DriverStatus

    class Config:
        from_attributes = True


# ---------- Trip ----------
class TripCreate(BaseModel):
    source: str
    destination: str
    vehicle_id: int
    driver_id: int
    cargo_weight: float
    planned_distance: float
    revenue: float = 0


class TripComplete(BaseModel):
    actual_distance: float
    fuel_consumed: float


class TripOut(BaseModel):
    id: int
    source: str
    destination: str
    vehicle_id: int
    driver_id: int
    cargo_weight: float
    planned_distance: float
    actual_distance: Optional[float]
    fuel_consumed: Optional[float]
    revenue: float
    status: TripStatus
    created_at: datetime.datetime
    dispatched_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


# ---------- Maintenance ----------
class MaintenanceCreate(BaseModel):
    vehicle_id: int
    description: str
    cost: float = 0


class MaintenanceOut(BaseModel):
    id: int
    vehicle_id: int
    description: str
    cost: float
    status: MaintenanceStatus
    created_at: datetime.datetime
    closed_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


# ---------- Fuel ----------
class FuelLogCreate(BaseModel):
    vehicle_id: int
    liters: float
    cost: float
    date: Optional[datetime.datetime] = None


class FuelLogOut(BaseModel):
    id: int
    vehicle_id: int
    liters: float
    cost: float
    date: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Expense ----------
class ExpenseCreate(BaseModel):
    vehicle_id: int
    category: str
    amount: float
    description: Optional[str] = None
    date: Optional[datetime.datetime] = None


class ExpenseOut(BaseModel):
    id: int
    vehicle_id: int
    category: str
    amount: float
    description: Optional[str]
    date: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Dashboard / Reports ----------
class DashboardKPIs(BaseModel):
    active_vehicles: int
    available_vehicles: int
    vehicles_in_maintenance: int
    active_trips: int
    pending_trips: int
    drivers_on_duty: int
    fleet_utilization_pct: float


class VehicleReport(BaseModel):
    vehicle_id: int
    registration_number: str
    fuel_efficiency: float  # distance/fuel
    total_distance: float
    total_fuel: float
    operational_cost: float
    revenue: float
    roi: float