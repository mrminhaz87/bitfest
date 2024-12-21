import sqlite3
from typing import Dict, List, Any
from langchain_ollama.llms import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
import json

# Initialize LLMs
recipe_llm = OllamaLLM(model="llama3.1")  # For recipe search and general queries
ingredient_llm = OllamaLLM(model="llama3.1")   # For ingredient comparison

class IngredientDB:
    def __init__(self, db_path: str = "kitchen_inventory.db"):
        self.db_path = db_path

    def get_all_ingredients(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, quantity, unit FROM ingredients WHERE quantity > 0")
            results = cursor.fetchall()
            return [{"name": r[0], "quantity": r[1], "unit": r[2]} for r in results]

class RecipeProcessor:
    def __init__(self, file_path: str = "my_fav_recipes.txt"):
        self.file_path = file_path
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n=== Recipe", "\n## ", "\n\n"]
        )
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vectorstore = None
        self.load_and_process_recipes()

    def load_and_process_recipes(self):
        with open(self.file_path, 'r') as file:
            content = file.read()
        chunks = self.text_splitter.split_text(content)
        self.vectorstore = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            collection_name="recipes"
        )

    def get_relevant_recipes(self, query: str, k: int = 3) -> List[str]:
        results = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

class KitchenBuddy:
    def __init__(self):
        self.db = IngredientDB()
        self.recipe_processor = RecipeProcessor()
        
        # Define the ingredient checking prompt
        self.check_prompt = PromptTemplate.from_template("""
        Your task is to check if a recipe can be made with available ingredients.

        Recipe Details:
        {recipe}

        Available Ingredients in Kitchen:
        {ingredients}

        Instructions:
        1. Extract the required ingredients from the recipe
        2. Compare with available ingredients
        3. Consider quantities where specified
        4. Respond with ONLY a single digit:
           - 1 if ALL required ingredients are available in sufficient quantities
           - 0 if ANY required ingredient is missing or insufficient

        Response (0 or 1 only):""")

    def check_ingredients_for_recipe(self, recipe: str, available_ingredients: List[Dict]) -> bool:
        """Check if a recipe can be made with available ingredients"""
        try:
            # Format available ingredients for better readability
            formatted_ingredients = "\n".join([
                f"- {ing['name']}: {ing['quantity']} {ing['unit']}"
                for ing in available_ingredients
            ])

            # Get LLM response
            result = ingredient_llm.invoke(
                self.check_prompt.format(
                    recipe=recipe,
                    ingredients=formatted_ingredients
                )
            )

            # Clean and validate response
            cleaned_result = result.strip().replace('\n', '').replace(' ', '')
            
            # Add logging for debugging
            print(f"LLM Response for ingredient check: {cleaned_result}")
            
            # Strict validation of response
            if cleaned_result not in ['0', '1']:
                print(f"Invalid LLM response format: {cleaned_result}")
                return False
                
            return bool(int(cleaned_result))
            
        except Exception as e:
            print(f"Error in ingredient check: {str(e)}")
            return False

    def find_suitable_recipe(self, query: str) -> Dict:
        """Main function to find a suitable recipe based on query and available ingredients"""
        try:
            # Get available ingredients
            available_ingredients = self.db.get_all_ingredients()
            
            # Get relevant recipes
            relevant_recipes = self.recipe_processor.get_relevant_recipes(query)
            
            if not relevant_recipes:
                return {
                    "status": "no_recipes_found",
                    "message": "No recipes found matching your query"
                }
            
            # Check each recipe until we find one we can make
            for recipe in relevant_recipes:
                can_make = self.check_ingredients_for_recipe(recipe, available_ingredients)
                
                if can_make:
                    return {
                        "status": "success",
                        "recipe": recipe,
                        "can_make": True,
                        "available_ingredients": available_ingredients
                    }
            
            # If no recipe can be made
            return {
                "status": "no_possible_recipe",
                "message": "Found recipes but missing required ingredients",
                "available_ingredients": available_ingredients,
                "suggested_recipes": relevant_recipes[:1]  # Return the first recipe as suggestion
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }

    def process_query(self, query: str) -> Dict:
        """Process a user query and return appropriate recipe recommendations"""
        result = self.find_suitable_recipe(query)
        return result

def main():
    # Initialize the kitchen buddy
    kitchen_buddy = KitchenBuddy()
    
    # Example queries to test
    test_queries = [
        "I want to make something sweet",
    ]
    
    # Test each query
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = kitchen_buddy.process_query(query)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()