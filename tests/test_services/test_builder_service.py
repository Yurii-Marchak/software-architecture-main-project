import pytest
from unittest.mock import AsyncMock
from core.services.builder_service import BuilderService


@pytest.fixture
def mock_build_repo():
    """Створюємо фейковий репозиторій бази даних для ізоляції бізнес-логіки."""
    return AsyncMock()

@pytest.fixture
def builder_service(mock_build_repo):
    """Ініціалізуємо сервіс із фейковим репозиторієм."""
    return BuilderService(build_repo=mock_build_repo)



def test_get_forced_filters_empty_state(builder_service):
    """Тест: Якщо збірка порожня, жодні примусові фільтри не застосовуються."""
    filters = builder_service.get_forced_filters(current_build_state={}, next_category="cpu")
    assert filters == {}

def test_get_forced_filters_motherboard_with_cpu(builder_service):
    """Тест: Вибір материнської плати вимагає сокет, що збігається з обраним CPU."""
    build_state = {"CPU": {"socket": "AM5", "name": "AMD Ryzen 5 7600"}}
    filters = builder_service.get_forced_filters(build_state, "motherboard")
    assert filters == {"socket": "AM5"}

def test_get_forced_filters_motherboard_without_cpu(builder_service):
    """Edge Case: Спроба вибрати плату, коли CPU ще не обрано (фільтрів не має бути)."""
    filters = builder_service.get_forced_filters({}, "motherboard")
    assert filters == {}

def test_get_forced_filters_memory_with_motherboard(builder_service):
    """Тест: Вибір пам'яті вимагає тип, який підтримується обраною материнкою."""
    build_state = {"Motherboard": {"supported_memory_type": "DDR5"}}
    filters = builder_service.get_forced_filters(build_state, "memory")
    assert filters == {"type": "DDR5"}

def test_get_forced_filters_cooler_with_cpu(builder_service):
    """Тест: Охолодження повинно підходити під сокет процесора."""
    build_state = {"CPU": {"socket": "LGA 1700"}}
    filters = builder_service.get_forced_filters(build_state, "cooler")
    assert filters == {"socket": "LGA 1700"}

def test_get_forced_filters_case_with_motherboard(builder_service):
    """Тест: Форм-фактор корпусу повинен відповідати розміру материнської плати."""
    build_state = {"Motherboard": {"size": "MicroATX"}}
    filters = builder_service.get_forced_filters(build_state, "case")
    assert filters == {"size": "MicroATX"}

def test_get_forced_filters_psu_calculation(builder_service):
    """Тест: Розрахунок мінімальної потужності БЖ (CPU Power + GPU Power + 200W)."""
    build_state = {
        "CPU": {"power": 105},
        "GPU": {"power": 320}
    }
    filters = builder_service.get_forced_filters(build_state, "psu")
    assert filters == {"min_power": ["625.0"]}

def test_get_forced_filters_psu_missing_power(builder_service):
    """Edge Case: Розрахунок БЖ, якщо для комплектуючих не вказана потужність (None або відсутня)."""
    build_state = {
        "CPU": {"power": None},
        "GPU": {}
    }
    filters = builder_service.get_forced_filters(build_state, "psu")
    assert filters == {"min_power": ["200.0"]}

def test_get_forced_filters_case_insensitivity(builder_service):
    """Edge Case: Сервіс повинен ігнорувати регістр назви категорії (MoTheRbOaRd == motherboard)."""
    build_state = {"CPU": {"socket": "AM4"}}
    filters = builder_service.get_forced_filters(build_state, "MoTheRbOaRd")
    assert filters == {"socket": "AM4"}



@pytest.mark.asyncio
async def test_save_build_success(builder_service, mock_build_repo):
    """Тест: Успішне збереження нової унікальної збірки."""

    mock_build_repo.get_by_name.return_value = None

    mock_build_repo.create.return_value = True

    components = {"CPU": "Intel i5", "GPU": "RTX 3060"}
    result = await builder_service.save_build("My Awesome PC", components)

    assert result is True

    mock_build_repo.get_by_name.assert_called_once_with("My Awesome PC")

    mock_build_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_save_build_duplicate_name(builder_service, mock_build_repo):
    """Edge Case: Спроба зберегти збірку з назвою, яка вже існує в БД."""

    mock_build_repo.get_by_name.return_value = {"name": "Existing PC", "components": {}}
    
    components = {"CPU": "AMD Ryzen 5"}
    result = await builder_service.save_build("Existing PC", components)

    assert result is False
    mock_build_repo.get_by_name.assert_called_once_with("Existing PC")

    mock_build_repo.create.assert_not_called()

@pytest.mark.asyncio
async def test_save_build_database_failure(builder_service, mock_build_repo):
    """Edge Case: Назва унікальна, але сталася помилка запису в саму БД."""
    mock_build_repo.get_by_name.return_value = None

    mock_build_repo.create.return_value = False

    result = await builder_service.save_build("Cursed PC", {"CPU": "Intel"})

    assert result is False
    mock_build_repo.create.assert_called_once()