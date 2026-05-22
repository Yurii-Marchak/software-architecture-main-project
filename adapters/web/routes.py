# adapters/web/routes.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from urllib.parse import urlencode

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

@router.get("/search", response_class=HTMLResponse)
async def global_search(
    request: Request,
    q: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Глобальний пошук по всіх категоріях"""
    # Додали pc_builds, щоб пошук працював і по готових збірках теж!
    categories = ["CPU", "Motherboard", "Memory", "GPU", "Case", "Cooler", "Storage", "PSU", "pc_builds"]
    results = []
    for cat in categories:
        items = await catalog_service.search_by_name(cat, q)
        # Додаємо назву категорії до кожного знайденого товару
        for item in items:
            item["category"] = cat 
        results.extend(items)
        
    return templates.TemplateResponse("catalog.html", {
        "request": request, 
        "category": "Результати пошуку", 
        "items": results, 
        "page": 1,
        # ФІКС: передаємо порожні словники, щоб HTML-шаблон не видавав помилку
        "current_filters": {}, 
        "forced_filters": {},
        "base_query_string": f"&q={q}"
    })

@router.get("/catalog/{category}", response_class=HTMLResponse)
async def catalog(
    request: Request, 
    category: str, 
    page: int = 1, 
    search: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service),
    builder_service: BuilderService = Depends(get_builder_service)
):
    # ФІКС 2: Додаємо виняток для pc_builds, щоб не ламати пошук у БД
    if category.lower() == "pc_builds":
        formatted_cat = "pc_builds"
    else:
        formatted_cat = category.capitalize() if category.lower() not in ["cpu", "gpu", "psu"] else category.upper()
    
    if search:
        items = await catalog_service.search_by_name(formatted_cat, search)
        filters = {}
        forced_filters = {}
        query_params_dict = {}
        base_query_string = f"&search={search}"
    else:
        query_params = request.query_params
        filters = {}
        query_params_dict = {}
        query_params_for_url = {}
        
        for k, v in query_params.multi_items():
            if k != "page":
                if k not in query_params_for_url:
                    query_params_for_url[k] = []
                query_params_for_url[k].append(v)
                
            if k in ["page", "search", "for_build"]: continue
            
            if k not in filters:
                filters[k] = []
                query_params_dict[k] = []
            filters[k].append(v)
            query_params_dict[k].append(v)
            
        forced_filters = {}
        if query_params.get("for_build"):
            build_state = request.session.get("build", {})
            forced_filters = builder_service.get_forced_filters(build_state, formatted_cat)
            for k, v in forced_filters.items():
                filters[k] = [v] if not isinstance(v, list) else v

        items = await catalog_service.get_filtered_catalog(formatted_cat, page=page, filters=filters)
        
        base_query_string = urlencode(query_params_for_url, doseq=True)
        if base_query_string:
            base_query_string = "&" + base_query_string
        
    return templates.TemplateResponse("catalog.html", {
        "request": request, 
        "category": formatted_cat, 
        "items": items, 
        "page": page,
        "forced_filters": forced_filters,
        "current_filters": query_params_dict,
        "base_query_string": base_query_string
    })

@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    category: str = Form(...),
    name: str = Form(...),
    price: float = Form(0),
    quantity: int = Form(1),
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    cart = request.session.get("cart", [])
    
    # ФІКС: Якщо додають готову збірку - розпаковуємо її на 8 окремих деталей
    if category.lower() == "pc_builds":
        build = await catalog_service.component_repo.get_by_name("pc_builds", name)
        if build and "components" in build:
            for comp_cat, comp_name in build["components"].items():
                comp_doc = await catalog_service.component_repo.get_by_name(comp_cat, comp_name)
                if comp_doc:
                    # Шукаємо чи є вже такий компонент в кошику, щоб збільшити quantity
                    found = False
                    for item in cart:
                        if item["name"] == comp_name:
                            item["quantity"] += quantity
                            found = True
                            break
                    if not found:
                        cart.append({
                            "category": comp_cat, 
                            "name": comp_name, 
                            "price": float(comp_doc.get("price", 0)), 
                            "quantity": quantity
                        })
            request.session["cart"] = cart
            request.session["flash_message"] = f"Всі 8 компонентів збірки '{name}' розпаковано і додано до кошика!"
            return RedirectResponse(url="/cart", status_code=303)
            
    # Стандартна логіка для окремих деталей (CPU, GPU тощо)
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
async def closed_orders(
    request: Request, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order_service: OrderService = Depends(get_order_service)
):
    """Закриті замовлення (чеки) з фільтром по даті"""
    orders = await order_service.get_filtered_orders(start_date, end_date)
    return templates.TemplateResponse("orders.html", {
        "request": request, 
        "orders": orders,
        "start_date": start_date,
        "end_date": end_date
    })

# --- ОБРОБНИКИ ДЛЯ ПОСТАВКИ (SUPPLY) ---

@router.get("/supply", response_class=HTMLResponse)
async def view_supply(request: Request):
    """Відображає вікно поставки"""
    return templates.TemplateResponse("supply.html", {"request": request})

@router.post("/supply/add")
async def add_to_supply(request: Request, category: str = Form(...), name: str = Form(...)):
    """Додає товар у список поставки (в сесію)"""
    supply_cart = request.session.get("supply_cart", [])
    
    for item in supply_cart:
        if item["name"] == name:
            item["quantity"] += 1
            request.session["supply_cart"] = supply_cart
            return RedirectResponse(url="/supply", status_code=303)
            
    supply_cart.append({"category": category, "name": name, "quantity": 1})
    request.session["supply_cart"] = supply_cart
    return RedirectResponse(url="/supply", status_code=303)

@router.post("/supply/clear")
async def clear_supply(request: Request):
    """Очищує каталог поставки у випадку помилки адміністратора"""
    request.session["supply_cart"] = []
    return RedirectResponse(url="/supply", status_code=303)

@router.post("/supply/commit")
async def commit_supply(
    request: Request,
    order_service: OrderService = Depends(get_order_service)
):
    """Кнопка 'Прийняти поставку': оновлює базу даних та очищує список"""
    supply_cart = request.session.get("supply_cart", [])
    if not supply_cart:
        request.session["flash_error"] = "Список поставки порожній."
        return RedirectResponse(url="/supply", status_code=303)

    form_data = await request.form()
    
    # Зчитуємо змінену кількість для кожного товару з HTML-форми
    for i, item in enumerate(supply_cart, start=1):
        qty_key = f"quantity_{i}"
        if qty_key in form_data:
            item["quantity"] = int(form_data[qty_key])

    # Збільшуємо кількість кожної позиції у базі даних (виклик бізнес-логіки)
    await order_service.receive_supply(supply_cart)
    
    request.session["supply_cart"] = []
    request.session["flash_message"] = "Поставку успішно прийнято! Склад оновлено."
    return RedirectResponse(url="/", status_code=303)


# --- ОБРОБНИКИ ДЛЯ КОНФІГУРАТОРА ПК (BUILDER) ---

@router.post("/builder/add")
async def add_to_build(
    request: Request,
    category: str = Form(...),
    name: str = Form(...),
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    build = request.session.get("build", {})
    
    if category.lower() == "pc_builds":
        formatted_cat = "pc_builds"
    else:
        formatted_cat = category.capitalize() if category.lower() not in ["cpu", "gpu", "psu"] else category.upper()
    
    component = await catalog_service.component_repo.get_by_name(formatted_cat, name)
    if component:
        # ФІКС 1: Зберігаємо лише необхідні поля, щоб уникнути переповнення Cookie (4KB)
        minimal_component = {
            "name": component.get("name"),
            "price": component.get("price", 0),
        }
        # Залишаємо технічні характеристики, що потрібні для примусових фільтрів на наступних етапах
        for key in ["socket", "power", "size", "supported_memory_type"]:
            if key in component and component[key] is not None:
                minimal_component[key] = component[key]
                
        build[formatted_cat] = minimal_component
        request.session["build"] = build

    build_order = ["CPU", "Motherboard", "Memory", "Storage", "Cooler", "GPU", "Case", "PSU"]
    try:
        current_idx = build_order.index(formatted_cat)
        if current_idx + 1 < len(build_order):
            next_cat = build_order[current_idx + 1].lower()
            return RedirectResponse(url=f"/catalog/{next_cat}?for_build=true", status_code=303)
    except ValueError:
        pass
        
    return RedirectResponse(url="/builder", status_code=303)

@router.post("/builder/save")
async def save_build(
    request: Request,
    build_name: str = Form(...),
    builder_service: BuilderService = Depends(get_builder_service)
):
    build = request.session.get("build", {})
    if not build:
        request.session["flash_error"] = "Збірка порожня."
        return RedirectResponse(url="/builder", status_code=303)

    components_names = {cat: item["name"] for cat, item in build.items()}
    success = await builder_service.save_build(build_name, components_names)
    
    if success:
        # Додаємо всі компоненти зі збірки у загальний кошик покупок
        cart = request.session.get("cart", [])
        for cat, comp in build.items():
            cart.append({
                "category": cat,
                "name": comp["name"],
                "price": comp.get("price", 0),
                "quantity": 1
            })
        request.session["cart"] = cart
        request.session["build"] = {} 
        request.session["flash_message"] = f"Збірку '{build_name}' збережено! Всі комплектуючі додано в кошик."
        return RedirectResponse(url="/", status_code=303)
    else:
        request.session["flash_error"] = f"Назва '{build_name}' вже зайнята."
        return RedirectResponse(url="/builder", status_code=303)
# --- ДОДАТКОВІ ОБРОБНИКИ ЗГІДНО ШАБЛОНІВ ---

@router.post("/cart/clear")
async def clear_cart(request: Request):
    """Очищення кошика"""
    request.session["cart"] = []
    return RedirectResponse(url="/cart", status_code=303)

@router.get("/client-info")
async def client_info(
    request: Request,
    email: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Отримання інформації про клієнта з модального вікна"""
    user = await order_service.user_repo.get_by_email(email)
    
    if not user:
        request.session["flash_error"] = f"Клієнта з email '{email}' не знайдено."
    else:
        orders_text = ", ".join(user.order_ids) if user.order_ids else "Немає минулих замовлень"
        request.session["flash_message"] = f"Клієнт: {user.first_name} {user.last_name} | Телефон: {user.phone} | Історія чеків: {orders_text}"
        
    return RedirectResponse(url="/", status_code=303)