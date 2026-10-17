from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProveedorSchema(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del proveedor")
    contacto: str = Field(..., min_length=1, description="Contacto del proveedor")


class ProductBase(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    descripcion: str = Field(..., min_length=1, description="Descripción del producto")
    categoria: str = Field(..., min_length=1, description="Categoría a la que pertenece el producto")
    precio: float = Field(..., ge=0, description="Precio numérico no negativo")
    stock: int = Field(..., ge=0, description="Cantidad disponible, entero no negativo")
    marca: str = Field(..., min_length=1, description="Marca del producto")
    estado: str = Field(..., min_length=1, description="Estado del producto")
    etiquetas: List[str] = Field(default_factory=list, description="Lista de etiquetas descriptivas")
    proveedor: ProveedorSchema = Field(..., description="Datos de contacto y nombre del proveedor")


class ProductCreate(ProductBase):
    """Esquema base para la creación de productos en futuras funcionalidades."""
    pass


class ProductResponse(ProductBase):
    """Esquema base de respuesta con serialización de identificador MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id", description="Identificador único serializado como cadena")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "_id": "60c72b2f9b1d8b2bad000001",
                "nombre": "Teclado mecánico",
                "descripcion": "Teclado USB para computadora",
                "categoria": "Periféricos",
                "precio": 350.0,
                "stock": 25,
                "marca": "Logitech",
                "estado": "Disponible",
                "etiquetas": ["teclado", "USB", "gaming"],
                "proveedor": {
                    "nombre": "Proveedor Central",
                    "contacto": "ventas@example.com"
                }
            }
        }
    )
