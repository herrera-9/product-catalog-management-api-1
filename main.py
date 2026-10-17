from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from api.v1.router import router as api_v1_router
from core.database import ping_database

app = FastAPI(
    title="Catálogo de Productos API",
    description="API REST para la gestión del catálogo de productos con FastAPI y MongoDB Atlas.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["General"])
def root():
    """Endpoint raíz que retorna mensaje de bienvenida."""
    return {
        "mensaje": "Bienvenido a la API del Catálogo de Productos",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Salud"])
def health_check():
    """
    Endpoint de comprobación de salud que verifica el estado de la aplicación
    y realiza un ping a MongoDB devolviendo una respuesta controlada.
    """
    db_ok, db_message = ping_database()
    response_data = {
        "status": "healthy" if db_ok else "unhealthy",
        "app": "Catálogo de Productos API",
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "message": db_message
        }
    }
    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=response_data)
