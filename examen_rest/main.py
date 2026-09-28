from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base, SessionLocal, engine, get_db


class LaptopCreate(BaseModel):
    marca: str
    modelo: str
    ram_gb: int


class LaptopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    marca: str
    modelo: str
    ram_gb: int
    disponible: bool


def preparar_base_de_datos() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(models.Laptop.id).limit(1)) is None:
            db.add_all(
                [
                    models.Laptop(
                        marca="Dell",
                        modelo="Latitude 5440",
                        ram_gb=16,
                        disponible=True,
                    ),
                    models.Laptop(
                        marca="Lenovo",
                        modelo="ThinkPad E14",
                        ram_gb=8,
                        disponible=False,
                    ),
                    models.Laptop(
                        marca="HP",
                        modelo="ProBook 450",
                        ram_gb=16,
                        disponible=True,
                    ),
                ]
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    preparar_base_de_datos()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def inicio():
    return {"mensaje": "API del laboratorio de cómputo"}


@app.get("/laptops", response_model=list[LaptopResponse])
def listar_laptops(db: Session = Depends(get_db)):
    return db.scalars(select(models.Laptop).order_by(models.Laptop.id)).all()


@app.get("/laptops/disponibles", response_model=list[LaptopResponse])
def listar_laptops_disponibles(db: Session = Depends(get_db)):
    consulta = (
        select(models.Laptop)
        .where(models.Laptop.disponible.is_(True))
        .order_by(models.Laptop.id)
    )
    return db.scalars(consulta).all()


@app.get("/laptops/{laptop_id}", response_model=LaptopResponse)
def obtener_laptop(laptop_id: int, db: Session = Depends(get_db)):
    laptop = db.get(models.Laptop, laptop_id)
    if laptop is None:
        raise HTTPException(status_code=404, detail="Laptop no encontrada")
    return laptop


@app.post(
    "/laptops",
    response_model=LaptopResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_laptop(datos: LaptopCreate, db: Session = Depends(get_db)):
    laptop = models.Laptop(**datos.model_dump(), disponible=True)
    db.add(laptop)
    db.commit()
    db.refresh(laptop)
    return laptop
