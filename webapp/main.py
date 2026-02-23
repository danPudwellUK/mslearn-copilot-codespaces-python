import os
import base64
import sqlite3
from typing import Union
from os.path import dirname, abspath, join
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")
DB_PATH = join(current_dir, "recipes.db")

app = FastAPI()
app.mount("/ui", StaticFiles(directory=static_path), name="ui")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS recipes "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, ingredients TEXT NOT NULL, instructions TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


init_db()


class Body(BaseModel):
    length: Union[int, None] = 20


class Recipe(BaseModel):
    name: str
    ingredients: str
    instructions: str


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.post('/generate')
def generate(body: Body):
    """
    Generate a pseudo-random token ID of twenty characters by default. Example POST request body:

    {
        "length": 20
    }
    """
    string = base64.b64encode(os.urandom(64))[:body.length].decode('utf-8')
    return {'token': string}


@app.get('/recipes')
def list_recipes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM recipes").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get('/recipes/{recipe_id}')
def get_recipe(recipe_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return dict(row)


@app.post('/recipes', status_code=201)
def create_recipe(recipe: Recipe):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO recipes (name, ingredients, instructions) VALUES (?, ?, ?)",
        (recipe.name, recipe.ingredients, recipe.instructions)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "name": recipe.name, "ingredients": recipe.ingredients, "instructions": recipe.instructions}


@app.delete('/recipes/{recipe_id}', status_code=204)
def delete_recipe(recipe_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
    finally:
        conn.close()