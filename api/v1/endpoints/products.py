import re
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

from core.database import get_products_collection
from schemas.products import ProductCreate, ProductResponse, ProductUpdate, ProductDeleteResponse
from utils.mongo import is_valid_object_id, serialize_doc, serialize_docs

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


@router.get(
    "/search",
    response_model=List[ProductResponse],
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Buscar productos por nombre",
    description="Permite buscar productos en el catálogo que coincidan de forma parcial con el nombre especificado, ignorando mayúsculas y minúsculas.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de productos coincidentes obtenida exitosamente"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Parámetro de búsqueda omitido, vacío o inválido"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Base de datos temporalmente no disponible"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error interno en la base de datos"
        }
    }
)
def search_products(
    name: str = Query(..., description="Término o fragmento del nombre a buscar"),
    collection: Collection = Depends(get_products_collection)
):
    """
    Busca productos en MongoDB cuyo campo 'nombre' contenga la cadena proporcionada.
    La búsqueda es insensible a mayúsculas/minúsculas y soporta coincidencias parciales.
    Rechaza valores vacíos o con solo espacios con HTTP 422.
    Devuelve HTTP 200 con la lista de productos encontrados o [] si no hay coincidencias.
    """
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El parámetro de búsqueda 'name' no puede estar vacío ni contener solo espacios."
        )

    clean_name = name.strip()
    escaped_name = re.escape(clean_name)

    query = {
        "nombre": {
            "$regex": escaped_name,
            "$options": "i"
        }
    }

    try:
        cursor = collection.find(query)
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


@router.get(
    "/category",
    include_in_schema=False,
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
)
def filter_products_by_category_empty():
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="La categoría no puede estar vacía ni contener solo espacios en blanco."
    )


@router.get(
    "/category/{categoria}",
    response_model=List[ProductResponse],
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Filtrar productos por categoría",
    description="Permite obtener todos los productos que pertenezcan a una categoría específica, sin distinguir mayúsculas y minúsculas.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista de productos filtrados por categoría obtenida exitosamente"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Categoría vacía o compuesta únicamente por espacios"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Base de datos temporalmente no disponible"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error interno en la base de datos"
        }
    }
)
def filter_products_by_category(
    categoria: str,
    collection: Collection = Depends(get_products_collection)
):
    """
    Filtra productos por coincidencia exacta de categoría (case-insensitive).
    Rechaza categorías vacías o compuestas por espacios con HTTP 422.
    Devuelve HTTP 200 con la lista de productos encontrados o [] si no hay coincidencias.
    """
    if not categoria or not categoria.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La categoría no puede estar vacía ni contener solo espacios en blanco."
        )

    clean_category = categoria.strip()
    escaped_category = re.escape(clean_category)

    query = {
        "categoria": {
            "$regex": f"^{escaped_category}$",
            "$options": "i"
        }
    }

    try:
        cursor = collection.find(query)
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


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Consultar producto por identificador",
    description="Permite consultar los datos detallados de un producto mediante su identificador único de MongoDB (ObjectId).",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Producto no encontrado"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Identificador inválido (no es un ObjectId válido)"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Base de datos temporalmente no disponible"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Error interno en la base de datos"}
    }
)
def get_product_by_id(
    product_id: str,
    collection: Collection = Depends(get_products_collection)
):
    """
    Valida el formato del ObjectId, consulta el producto por _id y lo devuelve.
    Retorna 422 si el identificador es inválido, 404 si no existe, o 200 con el producto.
    """
    if not is_valid_object_id(product_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Identificador inválido: '{product_id}' no es un ObjectId válido."
        )

    try:
        doc = collection.find_one({"_id": ObjectId(product_id)})
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

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con identificador '{product_id}' no encontrado."
        )

    return serialize_doc(doc)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Actualizar producto por identificador",
    description="Permite actualizar de forma completa o individual los campos editables de un producto existente mediante su ObjectId.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Producto no encontrado"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Identificador o datos de entrada inválidos"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Base de datos temporalmente no disponible"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Error interno en la base de datos"}
    }
)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    collection: Collection = Depends(get_products_collection)
):
    """
    Actualiza los campos editables de un producto existente en MongoDB.
    Valida el identificador ObjectId y los campos editables provistos.
    Devuelve el producto actualizado o los códigos de error correspondientes (404, 422, 500, 503).
    """
    if not is_valid_object_id(product_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Identificador inválido: '{product_id}' no es un ObjectId válido."
        )

    update_data = product_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe proporcionar al menos un campo editable para actualizar."
        )

    # Asegurar que no se modifique directamente _id ni id
    update_data.pop("_id", None)
    update_data.pop("id", None)

    oid = ObjectId(product_id)

    try:
        existing_doc = collection.find_one({"_id": oid})
        if existing_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con identificador '{product_id}' no encontrado."
            )

        collection.update_one({"_id": oid}, {"$set": update_data})
        updated_doc = collection.find_one({"_id": oid})
    except HTTPException:
        raise
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

    if updated_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con identificador '{product_id}' no encontrado."
        )

    return serialize_doc(updated_doc)


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar producto por identificador",
    description="Elimina físicamente un producto del catálogo mediante su identificador único de MongoDB (ObjectId).",
    responses={
        status.HTTP_200_OK: {
            "description": "Producto eliminado correctamente",
            "content": {"application/json": {"example": {"mensaje": "Producto eliminado correctamente"}}}
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Identificador inválido",
            "content": {"application/json": {"example": {"detail": "El identificador del producto no es válido."}}}
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Producto no encontrado",
            "content": {"application/json": {"example": {"detail": "Producto no encontrado."}}}
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Base de datos temporalmente no disponible",
            "content": {"application/json": {"example": {"detail": "Base de datos temporalmente no disponible."}}}
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error interno en la base de datos",
            "content": {"application/json": {"example": {"detail": "Error interno al procesar la solicitud en la base de datos."}}}
        }
    }
)
def delete_product(
    product_id: str,
    collection: Collection = Depends(get_products_collection)
):
    """
    Elimina físicamente un producto de la colección según su ObjectId.
    Retorna 200 con mensaje si deleted_count == 1.
    Retorna 400 si el identificador no tiene formato ObjectId válido.
    Retorna 404 si el producto no existe en la base de datos.
    Retorna 503 en caídas de conexión o 500 en otros errores de PyMongo.
    """
    if not is_valid_object_id(product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El identificador del producto no es válido."
        )

    oid = ObjectId(product_id)

    try:
        result = collection.delete_one({"_id": oid})
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

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado."
        )

    return {"mensaje": "Producto eliminado correctamente"}


