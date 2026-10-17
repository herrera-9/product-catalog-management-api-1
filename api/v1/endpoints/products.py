from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

from core.database import get_products_collection
from schemas.products import ProductCreate, ProductResponse
from utils.mongo import serialize_docs

router = APIRouter(prefix="/products", tags=["Productos"])


@router.post(
    "",
    response_model=ProductResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo producto",
    description="Permite registrar un nuevo producto en el catálogo validando sus campos comerciales, técnicos y de proveedor."
)
def create_product(
    product_in: ProductCreate,
    collection: Collection = Depends(get_products_collection)
):
    """
    Registra un nuevo producto en la colección de MongoDB.
    Valida los datos y devuelve el documento con su identificador generado como cadena.
    """
    try:
        product_data = product_in.model_dump()
        result = collection.insert_one(product_data)

        generated_id = str(result.inserted_id)
        product_data["id"] = generated_id
        product_data["_id"] = generated_id

        return product_data
    except (ConnectionFailure, ServerSelectionTimeoutError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos temporalmente no disponible."
        )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la solicitud en la base de datos."
        )


@router.get(
    "",
    response_model=List[ProductResponse],
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Listar todos los productos",
    description="Obtiene y devuelve la lista completa de productos registrados en el catálogo. Retorna una lista vacía si no hay productos."
)
def list_products(
    collection: Collection = Depends(get_products_collection)
):
    """
    Consulta todos los productos registrados en MongoDB.
    Devuelve HTTP 200 con la lista de productos o [] si la colección está vacía.
    """
    try:
        cursor = collection.find({})
        docs = list(cursor)
        return serialize_docs(docs)
    except (ConnectionFailure, ServerSelectionTimeoutError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos temporalmente no disponible."
        )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la solicitud en la base de datos."
        )
