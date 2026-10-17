from typing import Any, Dict, List, Optional
from bson import ObjectId


def is_valid_object_id(id_str: str) -> bool:
    """Verifica si una cadena de texto tiene el formato válido de un ObjectId."""
    if not isinstance(id_str, str):
        return False
    return ObjectId.is_valid(id_str)


def object_id_to_str(oid: Any) -> str:
    """Convierte un ObjectId o cualquier identificador compatible a cadena de texto."""
    if isinstance(oid, ObjectId):
        return str(oid)
    return str(oid) if oid is not None else ""


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Serializa un documento individual de MongoDB convirtiendo su campo '_id'
    a cadena de texto. Devuelve None si el documento recibido es nulo.
    """
    if doc is None:
        return None
    data = dict(doc)
    if "_id" in data and data["_id"] is not None:
        data["_id"] = str(data["_id"])
    return data


def serialize_docs(docs: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Serializa una lista de documentos de MongoDB, aplicando serialize_doc a cada uno.
    Devuelve una lista vacía si la entrada es nula o vacía.
    """
    if not docs:
        return []
    return [serialize_doc(d) for d in docs if d is not None]
