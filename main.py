# main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from adapters.web.routes import router

app = FastAPI(title="Система управління складом комп'ютерної техніки")

# Підключення механізму сесій (необхідно для збереження стану Кошика та Збірки ПК)
app.add_middleware(SessionMiddleware,
                   secret_key="super-secret-key-for-coursework")

templates = Jinja2Templates(directory="templates")

# Підключення роутера з усіма сторінками
app.include_router(router)

# Глобальний обробник винятків (надійна система обробки винятків)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Перехоплює бізнес-помилки (наприклад, клієнт не існує, нестача товару на складі)
    і гарно виводить їх адміністратору.
    """
    request.session["flash_error"] = str(exc)
    # Повертаємо на головну сторінку з повідомленням про помилку
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
        status_code=400
    )

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
