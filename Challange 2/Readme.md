# Kitchen Inventory & Recipe Manager API
Version: 0.1.5

- Route: /ingredients/
Method: GET
Description: Get all ingredients
Sample Response:
```json
[
  {
    "name": "Flour",
    "quantity": 500,
    "unit": "grams"
  }
]
```

- Route: /ingredients/
Method: POST
Description: Add a new ingredient to the inventory
Required Fields: name, quantity, unit
Sample Payload:
```json
{
  "name": "Sugar",
  "quantity": 250,
  "unit": "grams"
}
```
Sample Response:
```json
{
  "status": "success"
}
```

- Route: /ingredients/{ingredient_id}
Method: PUT
Description: Update ingredient quantity and unit
Parameters:
  - ingredient_id: integer (path parameter, required)
Required Fields: quantity
Optional Fields: unit
Sample Payload:
```json
{
  "quantity": 300,
  "unit": "grams"
}
```
Sample Response:
```json
{
  "status": "success"
}
```

- Route: /ingredients/{ingredient_id}
Method: DELETE
Description: Delete an ingredient
Parameters:
  - ingredient_id: integer (path parameter, required)
Sample Response:
```json
{
  "status": "success"
}
```

- Route: /recipes/text/
Method: POST
Description: Add a new recipe from text
Parameters:
  - recipe_text: string (query parameter, required)
Sample Query:
```
/recipes/text/?recipe_text=Mix 2 cups flour with 1 cup sugar...
```
Sample Response:
```json
{
  "status": "success"
}
```

- Route: /recipes/image/
Method: POST
Description: Add a new recipe from an image using EasyOCR
Content-Type: multipart/form-data
Required Fields: file (binary)
Sample Payload:
```
file: [binary image file]
```
Sample Response:
```json
{
  "status": "success"
}
```

Error Response (422 Validation Error):
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "error message",
      "type": "error type"
    }
  ]
}
```

## Data Schemas

### Ingredient
```json
{
  "name": "string",
  "quantity": "number",
  "unit": "string"
}
```

### IngredientUpdate
```json
{
  "quantity": "number",
  "unit": "string | null"
}
```