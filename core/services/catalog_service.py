# core/services/catalog_service.py
from typing import List, Dict, Any
from core.ports.repository import IComponentRepository


class CatalogService:
    def __init__(self, component_repo: IComponentRepository):
        # Впровадження залежностей (Dependency Injection)
        self.component_repo = component_repo

    async def get_filtered_catalog(self, category: str, page: int = 1, filters: Dict[str, Any] = None) -> List[dict]:
        all_items = await self.component_repo.get_all_by_category(category)

        # --- ФІКС: Збагачення готових збірок (ціна, фото, деталі) ---
        if category.lower() == "pc_builds":
            for item in all_items:
                total_price = 0
                case_img = ""
                comp_details = {}

                # Проходимося по всіх 8 комплектуючих збірки
                for cat, name in item.get("components", {}).items():
                    comp_doc = await self.component_repo.get_by_name(cat, name)
                    if comp_doc:
                        total_price += float(comp_doc.get("price", 0))
                        comp_details[cat] = comp_doc
                        # Якщо це корпус - забираємо його фото як головне фото збірки
                        if cat.lower() == "case":
                            case_img = comp_doc.get("image", "")

                item["price"] = total_price
                # Якщо фото корпусу немає, ставимо заглушку
                item["image"] = case_img if case_img else "https://via.placeholder.com/150"
                item["components_details"] = comp_details
        # ------------------------------------------------------------

        if filters:
            for key, value_list in filters.items():
                if not value_list:
                    continue

                clean_values = [v for v in value_list if str(v).strip() != ""]
                if not clean_values:
                    continue

                try:
                    if key == "min_price":
                        all_items = list(filter(lambda x: float(
                            x.get('price', 0)) >= float(clean_values[0]), all_items))
                    elif key == "max_price":
                        all_items = list(filter(lambda x: float(
                            x.get('price', 0)) <= float(clean_values[0]), all_items))
                    elif key == "min_frequency":
                        all_items = list(filter(lambda x: float(
                            x.get('frequency', 0)) >= float(clean_values[0]), all_items))
                    elif key == "max_frequency":
                        all_items = list(filter(lambda x: float(
                            x.get('frequency', 0)) <= float(clean_values[0]), all_items))
                    elif key == "min_power":
                        all_items = list(filter(lambda x: float(
                            x.get('power', 0)) >= float(clean_values[0]), all_items))
                    elif isinstance(value_list, list):
                        all_items = list(filter(lambda x: str(
                            x.get(key)) in clean_values, all_items))
                except ValueError:
                    continue

        start_idx = (page - 1) * 20
        end_idx = start_idx + 20

        return all_items[start_idx:end_idx]

    async def search_by_name(self, category: str, partial_name: str) -> List[dict]:
        """Пошук за частиною назви тільки у вказаній категорії (з урахуванням регістру)."""
        all_items = await self.component_repo.get_all_by_category(category)

        # Функціональна фільтрація: залишаємо тільки ті, де partial_name є в назві
        matched_items = list(
            filter(lambda x: partial_name.lower() in x.get('name', '').lower(), all_items))

        return matched_items
