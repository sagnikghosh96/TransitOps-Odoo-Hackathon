from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth_router, vehicles, drivers, trips, maintenance, fuel, expenses, dashboard, reports
from .seed import seed

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TransitOps API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(vehicles.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(maintenance.router)
app.include_router(fuel.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup():
    seed()


@app.get("/")
def root():
    return {"status": "ok", "service": "TransitOps API"}


@app.get("/health")
def health():
    return {"status": "healthy"}