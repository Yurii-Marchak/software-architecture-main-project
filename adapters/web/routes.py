# adapters/web/routes.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from core.services.catalog_service import CatalogService
from core.services.builder_service import BuilderService
from core.services.order_service import OrderService
from core.models.user import User

from adapters.web.dependencies import get_catalog_service, get_builder_service, get_order_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Головне вікно адміністратора"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/register")
async def register_client(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    order_service: OrderService = Depends(get_order_service)
):
    """Реєстрація клієнта з валідацією Pydantic"""
    try:
        new_user = User(email=email, first_name=first_name, last_name=last_name, phone=phone)
        await order_service.user_repo.create(new_user)
        # Додаємо повідомлення про успіх у сесію
        request.session["flash_message"] = f"Клієнта {email} успішно зареєстровано!"
    except Exception as e:
        request.session["flash_error"] = f"Помилка реєстрації: {str(e)}"
    
    return RedirectResponse(url="/", status_code=303)

@router.get("/catalog/{category}", response_class=HTMLResponse)
async def catalog(
    request: Request, 
    category: str, 
    page: int = 1, 
    search: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Секція каталог з пошуком та пагінацією"""
    if search:
        items = await catalog_service.search_by_name(category, search)
    else:
        # Для простоти передаємо пусті фільтри. У HTML формі можна додати передачу фільтрів.
        items = await catalog_service.get_filtered_catalog(category, page=page, filters={})
        
    return templates.TemplateResponse("catalog.html", {
        "request": request, 
        "category": category, 
        "items": items, 
        "page": page
    })

@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    category: str = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(1)
):
    """Додавання товару до кошика (в сесію)"""
    cart = request.session.get("cart", [])
    
    # Перевіряємо чи товар вже є в кошику
    for item in cart:
        if item["name"] == name:
            item["quantity"] += quantity
            request.session["cart"] = cart
            return RedirectResponse(url="/cart", status_code=303)
            
    cart.append({"category": category, "name": name, "price": price, "quantity": quantity})
    request.session["cart"] = cart
    return RedirectResponse(url="/cart", status_code=303)

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    """Вікно кошика"""
    cart = request.session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart)
    return templates.TemplateResponse("cart.html", {"request": request, "cart": cart, "total": total})

@router.post("/cart/checkout")
async def checkout(
    request: Request,
    email: str = Form(...),
    order_service: OrderService = Depends(get_order_service)
):
    """Завершити замовлення і оплатити"""
    cart = request.session.get("cart", [])
    if not cart:
        request.session["flash_error"] = "Кошик порожній."
        return RedirectResponse(url="/cart", status_code=303)
        
    try:
        order_id = await order_service.checkout(email, cart)
        request.session["cart"] = [] # Очищуємо кошик після успіху
        request.session["flash_message"] = f"Замовлення {order_id} створено! Чек відправлено на {email}."
    except ValueError as e:
        request.session["flash_error"] = str(e)
        
    return RedirectResponse(url="/", status_code=303)

@router.get("/builder", response_class=HTMLResponse)
async def pc_builder(request: Request):
    """Головне вікно конфігуратора ПК"""
    build = request.session.get("build", {})
    # Послідовність збірки ПК
    categories = ["CPU", "Motherboard", "Memory", "Storage", "Cooler", "GPU", "Case", "PSU"]
    return templates.TemplateResponse("builder.html", {"request": request, "build": build, "categories": categories})

@router.get("/orders", response_class=HTMLResponse)
async def closed_orders(request: Request, order_service: OrderService = Depends(get_order_service)):
    """Закриті замовлення (чеки)"""
    orders = await order_service.order_repo.get_all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})