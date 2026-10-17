
from fastapi import FastAPI
from api.v1.router import router

app = FastAPI(
    title="Catálogo de Productos API",
    description="API REST para la gestión del catálogo de productos",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "mensaje": "API del catálogo de productos funcionando"
    }
