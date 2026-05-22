# core/models/pc_build.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional


class PCBuild(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    name: str
    # Словник для збереження вибраних компонентів: {"CPU": "Intel Core i5...", "GPU": "..."}
    components: Dict[str, str]
