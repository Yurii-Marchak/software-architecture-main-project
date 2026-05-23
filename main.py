from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from adapters.web.routes import router

app = FastAPI(title="Система управління складом комп'ютерної техніки")

app.add_middleware(SessionMiddleware, secret_key="super-secret-key-for-coursework")

templates = Jinja2Templates(directory="templates")


app.include_router(router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Перехоплює бізнес-помилки (наприклад, клієнт не існує, нестача товару на складі)
    і гарно виводить їх адміністратору.
    """
    request.session["flash_error"] = str(exc)

    return templates.TemplateResponse(
        "index.html", 
        {"request": request}, 
        status_code=400
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)