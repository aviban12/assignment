from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from math import radians, sin, cos, sqrt, atan2

app = FastAPI()

Base = declarative_base()
engine = create_engine('sqlite:///database.db') 
Session = sessionmaker(bind=engine)
session = Session()

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, index=True)
    street = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    country = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    def __init__(self, street, city, state, country, latitude, longitude):
        self.street = street
        self.city = city
        self.state = state
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
        Base.metadata.create_all(bind=engine)

class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float

@app.post("/addresses", status_code=201)
def create_address(address: AddressCreate):
    try:
        new_address = Address(**address.dict())
        session.add(new_address)
        session.commit()
        return JSONResponse(status_code=201, content=jsonable_encoder(new_address))
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/addresses/{address_id}")
def get_address(address_id: int):
    address = session.query(Address).get(address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


class AddressUpdate(BaseModel):
    street: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float


@app.put("/addresses/{address_id}")
def update_address(address_id: int, address: AddressUpdate):
    existing_address = session.query(Address).get(address_id)
    if not existing_address:
        raise HTTPException(status_code=404, detail="Address not found")

    try:
        for field, value in address.dict().items():
            setattr(existing_address, field, value)
        session.commit()
        return existing_address
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/addresses/{address_id}")
def delete_address(address_id: int):
    address = session.query(Address).get(address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    try:
        session.delete(address)
        session.commit()
        return {"message": "Address deleted"}
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


class AddressSearch(BaseModel):
    latitude: float
    longitude: float
    distance: float


@app.post("/addresses/search")
def search_addresses(search: AddressSearch):
    addresses = session.query(Address).all()
    result = []
    for address in addresses:
        if calculate_distance(search.latitude, search.longitude, address.latitude, address.longitude) <= search.distance:
            result.append(address)
    return result


def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance
