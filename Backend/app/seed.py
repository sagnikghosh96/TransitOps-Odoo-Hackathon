import datetime
from .database import SessionLocal, engine, Base
from . import models, auth


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            demo_users = [
                ("Fiona Fleet", "fleetmanager@transitops.com", models.RoleEnum.fleet_manager),
                ("Dan Driver", "driver@transitops.com", models.RoleEnum.driver_role),
                ("Sara Safety", "safety@transitops.com", models.RoleEnum.safety_officer),
                ("Frank Finance", "finance@transitops.com", models.RoleEnum.financial_analyst),
            ]
            for name, email, role in demo_users:
                db.add(models.User(
                    name=name,
                    email=email,
                    hashed_password=auth.get_password_hash("password123"),
                    role=role,
                ))
            db.commit()
            print("Seeded demo users (password: password123 for all).")

        if db.query(models.Vehicle).count() == 0:
            vehicles = [
                models.Vehicle(registration_number="VAN-05", name_model="Ford Transit", type="Van",
                                max_load_capacity=500, odometer=12000, acquisition_cost=28000,
                                region="North", status=models.VehicleStatus.available),
                models.Vehicle(registration_number="TRK-11", name_model="Volvo FH16", type="Truck",
                                max_load_capacity=8000, odometer=54000, acquisition_cost=95000,
                                region="South", status=models.VehicleStatus.available),
                models.Vehicle(registration_number="TRK-12", name_model="Scania R500", type="Truck",
                                max_load_capacity=9000, odometer=88000, acquisition_cost=102000,
                                region="East", status=models.VehicleStatus.in_shop),
                models.Vehicle(registration_number="VAN-09", name_model="Mercedes Sprinter", type="Van",
                                max_load_capacity=650, odometer=30000, acquisition_cost=32000,
                                region="West", status=models.VehicleStatus.available),
            ]
            db.add_all(vehicles)
            db.commit()
            print("Seeded demo vehicles.")

        if db.query(models.Driver).count() == 0:
            drivers = [
                models.Driver(name="Alex Carter", license_number="LIC-1001", license_category="LMV",
                              license_expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=400),
                              contact_number="9876543210", safety_score=92,
                              status=models.DriverStatus.available),
                models.Driver(name="Maria Gomez", license_number="LIC-1002", license_category="HMV",
                              license_expiry_date=datetime.datetime.utcnow() + datetime.timedelta(days=200),
                              contact_number="9876543211", safety_score=88,
                              status=models.DriverStatus.available),
                models.Driver(name="Sam Wong", license_number="LIC-1003", license_category="HMV",
                              license_expiry_date=datetime.datetime.utcnow() - datetime.timedelta(days=5),
                              contact_number="9876543212", safety_score=75,
                              status=models.DriverStatus.available),
            ]
            db.add_all(drivers)
            db.commit()
            print("Seeded demo drivers.")

        if db.query(models.MaintenanceLog).count() == 0:
            truck = db.query(models.Vehicle).filter(
                models.Vehicle.registration_number == "TRK-12"
            ).first()
            if truck:
                db.add(models.MaintenanceLog(
                    vehicle_id=truck.id, description="Engine overhaul", cost=1500,
                    status=models.MaintenanceStatus.active,
                ))
                db.commit()
                print("Seeded demo maintenance log.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()