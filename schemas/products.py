from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


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


class ProductUpdate(BaseModel):
    """Esquema para la actualización parcial o total de un producto existente."""
    nombre: Optional[str] = Field(None, min_length=1, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, min_length=1, description="Descripción del producto")
    categoria: Optional[str] = Field(None, min_length=1, description="Categoría a la que pertenece el producto")
    precio: Optional[float] = Field(None, ge=0, description="Precio numérico no negativo")
    stock: Optional[int] = Field(None, ge=0, description="Cantidad disponible, entero no negativo")
    marca: Optional[str] = Field(None, min_length=1, description="Marca del producto")
    estado: Optional[str] = Field(None, min_length=1, description="Estado del producto")
    etiquetas: Optional[List[str]] = Field(None, description="Lista de etiquetas descriptivas")
    proveedor: Optional[ProveedorSchema] = Field(None, description="Datos de contacto y nombre del proveedor")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "nombre": "Laptop Lenovo IdeaPad Slim",
                "precio": 4200.00,
                "stock": 15
            }
        }
    )

    @field_validator("nombre", "descripcion", "categoria", "marca", "estado")
    @classmethod
    def validate_non_empty_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or not v.strip():
                raise ValueError("El campo no puede estar vacío ni contener solo espacios.")
            return v.strip()
        return v

    @field_validator("etiquetas")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            cleaned = []
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("Las etiquetas no pueden estar vacías ni contener solo espacios.")
                cleaned.append(tag.strip())
            return cleaned
        return v

    @model_validator(mode="after")
    def validate_fields_and_presence(self) -> "ProductUpdate":
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo editable para actualizar.")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"El campo '{field_name}' no puede ser nulo.")
        return self


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
