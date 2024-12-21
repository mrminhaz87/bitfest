from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import uvicorn
import pytesseract
from PIL import Image
import io
import os

app = FastAPI(title="Kitchen Inventory & Recipe Manager")

# Pydantic models for request validation
class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

class IngredientUpdate(BaseModel):
    quantity: float
    unit: Optional[str] = None

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect('kitchen_inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def append_to_recipes_file(recipe_text: str):
    """Append new recipe to my_fav_recipes.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recipe_entry = f"\n\n=== Recipe added on {timestamp} ===\n{recipe_text}\n"
    
    with open("my_fav_recipes.txt", "a", encoding='utf-8') as file:
        file.write(recipe_entry)

# Ingredient Management APIs
@app.post("/ingredients/", response_model=dict)
async def add_ingredient(ingredient: Ingredient):
    """Add a new ingredient to the inventory"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO ingredients (name, quantity, unit)
        VALUES (?, ?, ?)
        ''', (ingredient.name, ingredient.quantity, ingredient.unit))
        
        ingredient_id = cursor.lastrowid
        
        # Add to history
        cursor.execute('''
        INSERT INTO inventory_history 
        (ingredient_id, action_type, quantity_change, new_quantity)
        VALUES (?, ?, ?, ?)
        ''', (ingredient_id, 'add', ingredient.quantity, ingredient.quantity))
        
        conn.commit()
        return {"message": "Ingredient added successfully", "id": ingredient_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    finally:
        conn.close()

@app.get("/ingredients/", response_model=List[dict])
async def get_ingredients():
    """Get all ingredients"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ingredients')
    ingredients = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return ingredients

@app.put("/ingredients/{ingredient_id}", response_model=dict)
async def update_ingredient(ingredient_id: int, update: IngredientUpdate):
    """Update ingredient quantity and unit"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current quantity
        cursor.execute('SELECT quantity FROM ingredients WHERE id = ?', (ingredient_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        current_quantity = dict(current)['quantity']
        quantity_change = update.quantity - current_quantity
        
        # Update ingredient
        if update.unit:
            cursor.execute('''
            UPDATE ingredients 
            SET quantity = ?, unit = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (update.quantity, update.unit, ingredient_id))
        else:
            cursor.execute('''
            UPDATE ingredients 
            SET quantity = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (update.quantity, ingredient_id))
        
        # Add to history
        cursor.execute('''
        INSERT INTO inventory_history 
        (ingredient_id, action_type, quantity_change, new_quantity)
        VALUES (?, ?, ?, ?)
        ''', (ingredient_id, 'update', quantity_change, update.quantity))
        
        conn.commit()
        return {"message": "Ingredient updated successfully"}
    finally:
        conn.close()

@app.delete("/ingredients/{ingredient_id}", response_model=dict)
async def delete_ingredient(ingredient_id: int):
    """Delete an ingredient"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM ingredients WHERE id = ?', (ingredient_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        conn.commit()
        return {"message": "Ingredient deleted successfully"}
    finally:
        conn.close()

# Recipe Management APIs
@app.post("/recipes/text/", response_model=dict)
async def add_recipe_text(recipe_text: str):
    """Add a new recipe from text"""
    try:
        append_to_recipes_file(recipe_text)
        return {"message": "Recipe added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add recipe: {str(e)}")

@app.post("/recipes/image/", response_model=dict)
async def add_recipe_image(file: UploadFile = File(...)):
    """Add a new recipe from an image using OCR"""
    try:
        # Read and process the image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Perform OCR
        recipe_text = pytesseract.image_to_string(image)
        
        if not recipe_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from image")
        
        # Add extracted text to recipes file
        append_to_recipes_file(recipe_text)
        
        return {
            "message": "Recipe extracted and added successfully",
            "extracted_text": recipe_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process recipe image: {str(e)}")

if __name__ == "__main__":
    # Ensure recipes file exists
    if not os.path.exists("my_fav_recipes.txt"):
        with open("my_fav_recipes.txt", "w", encoding='utf-8') as f:
            f.write("=== My Favorite Recipes ===\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8007)