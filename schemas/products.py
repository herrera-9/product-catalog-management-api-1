from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProveedorSchema(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del proveedor")
    contacto: str = Field(..., min_length=1, description="Contacto del proveedor")

    @field_validator("nombre", "contacto")
    @classmethod
    def validate_non_empty_supplier(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v.strip()


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

    @field_validator("nombre", "descripcion", "categoria", "marca", "estado")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
        return v.strip()


class ProductCreate(ProductBase):
    """Esquema para la creación de un nuevo producto."""
    pass


class ProductResponse(ProductBase):
    """Esquema de respuesta que serializa el identificador de MongoDB."""
    id: str = Field(alias="_id", description="Identificador único serializado como cadena de texto")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "60c72b2f9b1d8b2bad000001",
                "nombre": "Laptop Lenovo IdeaPad",
                "descripcion": "Computadora portátil de 15 pulgadas con 8 GB de RAM y SSD de 512 GB",
                "categoria": "Computadoras",
                "precio": 4500.50,
                "stock": 10,
                "marca": "Lenovo",
                "estado": "activo",
                "etiquetas": ["laptop", "tecnologia", "oficina"],
                "proveedor": {
                    "nombre": "Distribuidora Tecnológica",
                    "contacto": "proveedor@ejemplo.com"
                }
            }
        }
    )
