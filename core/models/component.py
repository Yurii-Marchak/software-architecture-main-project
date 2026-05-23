from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class Component(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = Field(None, alias="_id")
    name: str
    image: str
    url: str
    price: float
    stock: int


class CPU(Component):
    brand: str
    socket: str
    speed: float
    coreCount: int
    threadCount: int
    power: int

class GPU(Component):
    brand: str
    VRAM: int
    resolution: str
    power: int

class Motherboard(Component):
    brand: str
    socket: str
    size: str
    supported_memory_type: str
    max_memory_sticks: int

class Memory(Component):
    type: str
    size: str
    frequency: int
    CAS_latency: str

class Storage(Component):
    type: str
    space: int

class Cooler(Component):
    type: str
    socket: str

class Case(Component):
    size: str

class PSU(Component):
    power: int
    size: str