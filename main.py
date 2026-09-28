from contextlib  import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Laptop

class LaptopCreate(BaseModel):
    marca: str
    modelo: str
    ram_gb: int

def laptop_a_dict(laptop: Laptop) -> dict:
    return {
        "id": laptop.id,
        "marca": laptop.marca,
        "modelo": laptop.modelo,
        "ram_gb": laptop.ram_gb,
        "disponible": laptop.disponible
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        primera_laptop = db.scalars(select(Laptop).limit(1)).first()

        if primera_laptop is None:
            db.add_all([
                Laptop(marca="Dell", modelo="Latitude 5440",
                       ram_gb=16, disponible=True),
                Laptop(marca="Lenovo", modelo="ThinkPad E14",
                       ram_gb=8, disponible=False),
                Laptop(marca="HP", modelo="ProBook 450",
                       ram_gb=16, disponible=True)
            ])
            db.commit()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
def inicio():
    return {"mensaje": "API del laboratorio de cómputo"}


@app.get("/laptops")
def listar_laptops(db: Session = Depends(get_db)):
    laptops = db.scalars(select(Laptop).order_by(Laptop.id)).all()
    return [laptop_a_dict(laptop) for laptop in laptops]


@app.get("/laptops/disponibles")
def listar_disponibles(db: Session = Depends(get_db)):
    laptops = db.scalars(
        select(Laptop)
        .where(Laptop.disponible == True)
        .order_by(Laptop.id)
    ).all()
    return [laptop_a_dict(laptop) for laptop in laptops]


@app.get("/laptops/{laptop_id}")
def obtener_laptop(laptop_id: int, db: Session = Depends(get_db)):
    laptop = db.get(Laptop, laptop_id)

    if laptop is None:
        raise HTTPException(status_code=404, detail="Laptop no encontrada")

    return laptop_a_dict(laptop)


@app.post("/laptops", status_code=201)
def crear_laptop(datos: LaptopCreate, db: Session = Depends(get_db)):
    laptop = Laptop(
        marca=datos.marca,
        modelo=datos.modelo,
        ram_gb=datos.ram_gb,
        disponible=True,
    )
    db.add(laptop)
    db.commit()
    db.refresh(laptop)

    return laptop_a_dict(laptop)