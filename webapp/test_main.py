import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Point to a temporary database file before importing main
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

import webapp.main as main_module
main_module.DB_PATH = _db_path
main_module.init_db()

from webapp.main import app

client = TestClient(app)


def setup_function():
    """Reset the database before each test."""
    conn = main_module.get_db()
    conn.execute("DELETE FROM recipes")
    conn.commit()
    conn.close()


def teardown_module():
    """Remove the temporary database after all tests."""
    try:
        os.unlink(_db_path)
    except OSError:
        pass


def test_create_recipe():
    response = client.post("/recipes", json={
        "name": "Pancakes",
        "ingredients": "flour, eggs, milk",
        "instructions": "Mix and fry"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Pancakes"
    assert "id" in data


def test_list_recipes():
    client.post("/recipes", json={"name": "Toast", "ingredients": "bread", "instructions": "Toast it"})
    response = client.get("/recipes")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_recipe():
    create_resp = client.post("/recipes", json={
        "name": "Omelette",
        "ingredients": "eggs, salt",
        "instructions": "Beat and cook"
    })
    recipe_id = create_resp.json()["id"]
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Omelette"


def test_get_recipe_not_found():
    response = client.get("/recipes/99999")
    assert response.status_code == 404


def test_delete_recipe():
    create_resp = client.post("/recipes", json={
        "name": "Soup",
        "ingredients": "water, vegetables",
        "instructions": "Boil everything"
    })
    recipe_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/recipes/{recipe_id}")
    assert delete_resp.status_code == 204

    # Confirm the deleted recipe returns 404
    get_resp = client.get(f"/recipes/{recipe_id}")
    assert get_resp.status_code == 404


def test_delete_recipe_not_found():
    response = client.delete("/recipes/99999")
    assert response.status_code == 404
