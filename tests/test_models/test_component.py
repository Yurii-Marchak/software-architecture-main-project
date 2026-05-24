import pytest
from pydantic import ValidationError
from core.models.component import CPU, GPU, Motherboard

def test_cpu_creation_success():
    """Тест: Успішне створення процесора з усіма обов'язковими полями."""
    cpu = CPU(
        name="AMD Ryzen 5", 
        price=250.0, 
        brand="AMD", 
        socket="AM4", 
        speed=3.7, 
        coreCount=6, 
        threadCount=12, 
        power=65,
        image="https://example.com/cpu.png",
        url="https://example.com/cpu",
        stock=10
    )
    assert cpu.brand == "AMD"
    assert cpu.socket == "AM4"
    assert cpu.stock == 10

def test_gpu_creation_success():
    """Тест: Успішне створення відеокарти з усіма обов'язковими полями."""
    gpu = GPU(
        name="RTX 3060", 
        price=350.0, 
        brand="NVIDIA", 
        VRAM=12, 
        resolution="1080p", 
        power=170,
        image="https://example.com/gpu.png",
        url="https://example.com/gpu",
        stock=5
    )
    assert gpu.VRAM == 12
    assert gpu.power == 170

def test_motherboard_creation_success():
    """Тест: Успішне створення материнської плати з усіма обов'язковими полями."""
    mb = Motherboard(
        name="ASUS B550", 
        price=120.0, 
        brand="AMD", 
        socket="AM4", 
        size="MicroATX", 
        supported_memory_type="DDR4", 
        max_memory_sticks=4,
        image="https://example.com/mb.png",
        url="https://example.com/mb",
        stock=15
    )
    assert mb.size == "MicroATX"
    assert mb.price == 120.0

def test_component_missing_fields():
    """Edge Case: Спроба створення компонента без базових полів (stock, image, url)."""
    with pytest.raises(ValidationError) as exc_info:

        CPU(name="Intel Core i9", price=500.0, brand="Intel")
        

    error_msg = str(exc_info.value).lower()
    assert "image" in error_msg
    assert "url" in error_msg
    assert "stock" in error_msg