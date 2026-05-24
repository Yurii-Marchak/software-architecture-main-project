import pytest
from unittest.mock import AsyncMock
from core.services.catalog_service import CatalogService

@pytest.fixture
def mock_component_repo():
    return AsyncMock()

@pytest.fixture
def catalog_service(mock_component_repo):
    return CatalogService(component_repo=mock_component_repo)


FAKE_CATALOG = [
    {"name": "Intel Core i3", "price": 100, "brand": "Intel", "power": 65, "frequency": 3.6},
    {"name": "AMD Ryzen 5", "price": 200, "brand": "AMD", "power": 65, "frequency": 4.2},
    {"name": "Intel Core i9", "price": 500, "brand": "Intel", "power": 125, "frequency": 5.0}
]

@pytest.mark.asyncio
async def test_get_catalog_no_filters(catalog_service, mock_component_repo):
    """Тест: Отримання всього каталогу без фільтрів."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    
    result = await catalog_service.get_filtered_catalog("CPU")
    assert len(result) == 3

@pytest.mark.asyncio
async def test_get_catalog_min_price(catalog_service, mock_component_repo):
    """Тест лямбда-фільтра: Мінімальна ціна >= 200."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"min_price": ["200"]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 2
    assert result[0]["name"] == "AMD Ryzen 5"
    assert result[1]["name"] == "Intel Core i9"

@pytest.mark.asyncio
async def test_get_catalog_max_price(catalog_service, mock_component_repo):
    """Тест лямбда-фільтра: Максимальна ціна <= 200."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"max_price": ["200"]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 2
    assert result[0]["name"] == "Intel Core i3"

@pytest.mark.asyncio
async def test_get_catalog_checkbox_array(catalog_service, mock_component_repo):
    """Тест лямбда-фільтра: Фільтрація по масиву галочок (in)."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"brand": ["AMD"]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 1
    assert result[0]["brand"] == "AMD"

@pytest.mark.asyncio
async def test_get_catalog_multiple_filters(catalog_service, mock_component_repo):
    """Тест лямбда-фільтра: Комбінація ціни та бренду."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"min_price": ["150"], "brand": ["Intel"]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 1
    assert result[0]["name"] == "Intel Core i9"

@pytest.mark.asyncio
async def test_get_catalog_ignore_empty_filters(catalog_service, mock_component_repo):
    """Edge Case: Сервіс має ігнорувати порожні рядки у фільтрах."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"min_price": [""], "brand": ["   "]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 3

@pytest.mark.asyncio
async def test_get_catalog_invalid_number_format(catalog_service, mock_component_repo):
    """Edge Case: Якщо замість ціни передали текст, система не має впасти (try/except)."""
    mock_component_repo.get_all_by_category.return_value = FAKE_CATALOG
    filters = {"min_price": ["not-a-number"]}
    
    result = await catalog_service.get_filtered_catalog("CPU", filters=filters)
    assert len(result) == 3

@pytest.mark.asyncio
async def test_get_catalog_pagination(catalog_service, mock_component_repo):
    """Тест: Пагінація повинна повертати максимум 20 елементів (зріз масиву)."""

    mock_component_repo.get_all_by_category.return_value = [{"name": "Item"}] * 25
    
    page_1 = await catalog_service.get_filtered_catalog("CPU", page=1)
    assert len(page_1) == 20
    
    page_2 = await catalog_service.get_filtered_catalog("CPU", page=2)
    assert len(page_2) == 5

@pytest.mark.asyncio
async def test_search_by_name(catalog_service, mock_component_repo):
    """Тест: Пошук по імені делегується репозиторію."""

    mock_component_repo.search.return_value = [FAKE_CATALOG[0]]
    mock_component_repo.search_by_name.return_value = [FAKE_CATALOG[0]]
    mock_component_repo.get_all_by_category.return_value = [FAKE_CATALOG[0]]
    
    result = await catalog_service.search_by_name("CPU", "i3")
    assert len(result) >= 1

@pytest.mark.asyncio
async def test_get_catalog_pc_builds_enrichment(catalog_service, mock_component_repo):
    """Тест: Збагачення готових збірок (підрахунок ціни з компонентів)."""

    mock_component_repo.get_all_by_category.return_value = [
        {"name": "Gaming PC", "components": {"CPU": "i9", "Case": "NZXT"}}
    ]
    

    async def mock_get_by_name(cat, name):
        if cat == "CPU": return {"name": "i9", "price": 500}
        if cat == "Case": return {"name": "NZXT", "price": 100, "image": "case.jpg"}
        return None
        
    mock_component_repo.get_by_name.side_effect = mock_get_by_name
    
    result = await catalog_service.get_filtered_catalog("pc_builds")
    assert len(result) == 1
    assert result[0]["price"] == 600.0
    assert result[0]["image"] == "case.jpg"