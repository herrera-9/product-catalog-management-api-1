import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure, PyMongoError

from main import app
from core.database import get_products_collection


class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        doc_copy = dict(doc)
        new_id = ObjectId()
        doc_copy["_id"] = new_id
        self.docs.append(doc_copy)

        class InsertResult:
            inserted_id = new_id

        return InsertResult()


class DbUnavailableCollection:
    def insert_one(self, doc):
        raise ConnectionFailure("Database unavailable simulated failure")


class DbErrorCollection:
    def insert_one(self, doc):
        raise PyMongoError("Internal database error simulated failure")


@pytest.fixture
def fake_collection():
    return FakeCollection()


@pytest.fixture
def client(fake_collection):
    app.dependency_overrides[get_products_collection] = lambda: fake_collection
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_product_payload():
    return {
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


def test_case_1_register_product_success(client, valid_product_payload):
    """Caso 1 – Registro correcto: HTTP 201, producto registrado, ID generado, campos conservados."""
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 201

    data = response.json()
    # Identificador generado
    assert "id" in data
    assert isinstance(data["id"], str)
    assert len(data["id"]) == 24
    assert ObjectId.is_valid(data["id"])

    # Campos conservados
    assert data["nombre"] == valid_product_payload["nombre"]
    assert data["descripcion"] == valid_product_payload["descripcion"]
    assert data["categoria"] == valid_product_payload["categoria"]
    assert data["precio"] == valid_product_payload["precio"]
    assert data["stock"] == valid_product_payload["stock"]
    assert data["marca"] == valid_product_payload["marca"]
    assert data["estado"] == valid_product_payload["estado"]
    assert data["etiquetas"] == valid_product_payload["etiquetas"]
    assert data["proveedor"]["nombre"] == valid_product_payload["proveedor"]["nombre"]
    assert data["proveedor"]["contacto"] == valid_product_payload["proveedor"]["contacto"]


def test_case_2_negative_price(client, valid_product_payload):
    """Caso 2 – Precio negativo: HTTP 422."""
    valid_product_payload["precio"] = -10.0
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 422


def test_case_3_negative_stock(client, valid_product_payload):
    """Caso 3 – Stock negativo: HTTP 422."""
    valid_product_payload["stock"] = -5
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 422


def test_case_4_missing_required_field_nombre(client, valid_product_payload):
    """Caso 4 – Campo obligatorio faltante: Omitir nombre -> HTTP 422."""
    del valid_product_payload["nombre"]
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 422


def test_case_5_incomplete_supplier(client, valid_product_payload):
    """Caso 5 – Proveedor incompleto: Omitir proveedor.contacto -> HTTP 422."""
    del valid_product_payload["proveedor"]["contacto"]
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 422


def test_case_6_invalid_data_etiquetas(client, valid_product_payload):
    """Caso 6 – Datos incorrectos: Enviar etiquetas con una estructura inválida -> HTTP 422."""
    valid_product_payload["etiquetas"] = "no-es-una-lista"
    response = client.post("/api/v1/products", json=valid_product_payload)
    assert response.status_code == 422


def test_case_7_database_unavailable(valid_product_payload):
    """Caso 7 – Base de datos no disponible: Respuesta controlada sin exponer datos sensibles."""
    app.dependency_overrides[get_products_collection] = lambda: DbUnavailableCollection()
    with TestClient(app) as test_client:
        response = test_client.post("/api/v1/products", json=valid_product_payload)
    app.dependency_overrides.clear()

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Base de datos temporalmente no disponible."
    # Asegurar que no expone cadenas de conexión ni trazas
    assert "Database unavailable simulated failure" not in data["detail"]


def test_case_7_database_internal_error(valid_product_payload):
    """Variante Caso 7 – Error interno de base de datos -> HTTP 500 controlado."""
    app.dependency_overrides[get_products_collection] = lambda: DbErrorCollection()
    with TestClient(app) as test_client:
        response = test_client.post("/api/v1/products", json=valid_product_payload)
    app.dependency_overrides.clear()

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Error interno al procesar la solicitud en la base de datos."


def test_swagger_and_openapi_registration(client):
    """Verifica que POST /api/v1/products aparezca documentado en OpenAPI y Swagger."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert "/api/v1/products" in schema["paths"]
    post_endpoint = schema["paths"]["/api/v1/products"]["post"]
    assert "201" in post_endpoint["responses"]

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200
