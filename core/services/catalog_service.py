# core/services/catalog_service.py
from typing import List, Dict, Any
from core.ports.repository import IComponentRepository

class CatalogService:
    def __init__(self, component_repo: IComponentRepository):
        # Впровадження залежностей (Dependency Injection)
        self.component_repo = component_repo

    async def get_filtered_catalog(self, category: str, page: int = 1, filters: Dict[str, Any] = None) -> List[dict]:
        """Отримує каталог з бази та застосовує фільтри через лямбда-вирази."""
        all_items = await self.component_repo.get_all_by_category(category)
        
        if filters:
            # Функціональний підхід: фільтрація списку словників через лямбди
            for key, value in filters.items():
                if value is None or value == "":
                    continue
                    
                if key == "min_price":
                    all_items = list(filter(lambda x: x.get('price', 0) >= float(value), all_items))
                elif key == "max_price":
                    all_items = list(filter(lambda x: x.get('price', 0) <= float(value), all_items))
                elif key == "coreCount_gt_16":
                    # Для галочки "> 16 ядер"
                    all_items = list(filter(lambda x: x.get('coreCount', 0) > 16, all_items))
                elif isinstance(value, list): 
                    # Якщо вибрано кілька варіантів (наприклад бренди: Intel і AMD)
                    all_items = list(filter(lambda x: x.get(key) in value, all_items))
                else:
                    # Точний збіг (наприклад socket)
                    all_items = list(filter(lambda x: str(x.get(key)).lower() == str(value).lower(), all_items))

        # Пагінація: максимум 20 позицій на сторінці
        start_idx = (page - 1) * 20
        end_idx = start_idx + 20
        
        return all_items[start_idx:end_idx]
        
    async def search_by_name(self, category: str, partial_name: str) -> List[dict]:
        """Пошук за частиною назви тільки у вказаній категорії (з урахуванням регістру)."""
        all_items = await self.component_repo.get_all_by_category(category)
        
        # Функціональна фільтрація: залишаємо тільки ті, де partial_name є в назві
        matched_items = list(filter(lambda x: partial_name.lower() in x.get('name', '').lower(), all_items))
        
        return matched_items