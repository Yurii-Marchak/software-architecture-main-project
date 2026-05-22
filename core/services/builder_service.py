# core/services/builder_service.py
from typing import Dict, Any
from core.ports.repository import IPCBuildRepository
from core.models.pc_build import PCBuild

class BuilderService:
    def __init__(self, build_repo: IPCBuildRepository):
        self.build_repo = build_repo

    def get_forced_filters(self, current_build_state: Dict[str, Any], next_category: str) -> Dict[str, Any]:
        """Аналізує поточний стан збірки та встановлює жорсткі обмеження для наступного кроку."""
        filters = {}
        cat = next_category.lower()
        
        if cat == "motherboard" and "CPU" in current_build_state:
            filters["socket"] = current_build_state["CPU"].get("socket")
            
        elif cat == "memory" and "Motherboard" in current_build_state:
            filters["type"] = current_build_state["Motherboard"].get("supported_memory_type")
            
        elif cat == "cooler" and "CPU" in current_build_state:
            filters["socket"] = current_build_state["CPU"].get("socket")
            
        elif cat == "case" and "Motherboard" in current_build_state:
            filters["size"] = current_build_state["Motherboard"].get("size")
            
        elif cat == "psu" and "CPU" in current_build_state and "GPU" in current_build_state:
            # power cpu + power gpu + 200
            req_power = float(current_build_state["CPU"].get("power", 0)) + float(current_build_state["GPU"].get("power", 0)) + 200
            filters["min_power"] = [str(req_power)]
            
        return filters
    async def save_build(self, name: str, components_names: Dict[str, str]) -> bool:
        """Перевіряє унікальність назви та зберігає конфігурацію в БД."""
        existing_build = await self.build_repo.get_by_name(name)
        if existing_build:
            return False # Збірка не унікальна
            
        new_build = PCBuild(name=name, components=components_names)
        return await self.build_repo.create(new_build)