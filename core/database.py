from typing import Optional, Tuple
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError
from core.config import settings

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Obtiene o inicializa de forma diferida (lazy) la instancia del cliente MongoDB."""
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
    return _client


def get_database() -> Database:
    """Obtiene la base de datos configurada."""
    client = get_client()
    return client[settings.MONGODB_DATABASE]


def get_products_collection() -> Collection:
    """Obtiene la colección de productos."""
    db = get_database()
    return db[settings.COLLECTION_NAME]


def ping_database() -> Tuple[bool, str]:
    """
    Ejecuta un ping sobre MongoDB para verificar el estado de la conexión.
    Retorna una tupla (conectado, mensaje) sin exponer credenciales ni datos sensibles.
    """
    try:
        client = get_client()
        client.admin.command("ping")
        return True, "Conexión con MongoDB exitosa"
    except PyMongoError:
        return False, "No se pudo conectar a la base de datos"
    except Exception:
        return False, "Error al verificar el estado de la base de datos"


def close_client() -> None:
    """Cierra la conexión activa del cliente MongoDB."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
