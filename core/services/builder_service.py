# core/services/builder_service.py
from typing import Dict, Any
from core.ports.repository import IPCBuildRepository
from core.models.pc_build import PCBuild

class BuilderService:
    def __init__(self, build_repo: IPCBuildRepository):
        self.build_repo = build_repo

    def get_forced_filters(self, current_build_state: Dict[str, Any], next_category: str) -> Dict[str, Any]:
        """
        Аналізує поточний стан збірки та повертає словник примусових фільтрів для наступного кроку.
        current_build_state виглядає так: {"CPU": {"socket": "LGA 1151", "power": 65}, "Motherboard": {...}}
        """
        filters = {}
        
        if next_category == "motherboard" and "CPU" in current_build_state:
            filters["socket"] = current_build_state["CPU"].get("socket")
            
        elif next_category == "memory" and "Motherboard" in current_build_state:
            filters["type"] = current_build_state["Motherboard"].get("supported_memory_type")
            
        elif next_category == "cooler" and "CPU" in current_build_state:
            filters["socket"] = current_build_state["CPU"].get("socket")
            
        elif next_category == "case" and "Motherboard" in current_build_state:
            filters["size"] = current_build_state["Motherboard"].get("size")
            
        elif next_category == "psu" and "CPU" in current_build_state and "GPU" in current_build_state:
            # Значення power cpu + значення power gpu + 200w
            required_power = current_build_state["CPU"].get("power", 0) + current_build_state["GPU"].get("power", 0) + 200
            filters["min_power"] = required_power
            
        return filters

    async def save_build(self, name: str, components_names: Dict[str, str]) -> bool:
        """Перевіряє унікальність назви та зберігає конфігурацію в БД."""
        existing_build = await self.build_repo.get_by_name(name)
        if existing_build:
            return False # Збірка не унікальна
            
        new_build = PCBuild(name=name, components=components_names)
        return await self.build_repo.create(new_build)