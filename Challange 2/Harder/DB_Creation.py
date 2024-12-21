import sqlite3
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_name='mofas_kitchen.db'):
        self.db_name = db_name
        
    def create_database(self):
        """Creates the SQLite database schema for Mofa's Kitchen Buddy application."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create ingredients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            quantity REAL DEFAULT 0,
            unit TEXT,
            expiry_date DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create recipes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cuisine_type TEXT,
            preparation_time INTEGER,
            difficulty_level TEXT,
            taste_profile TEXT,
            instructions TEXT NOT NULL,
            servings INTEGER,
            rating REAL DEFAULT 0,
            source TEXT,
            is_favorite BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create recipe_ingredients junction table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
            PRIMARY KEY (recipe_id, ingredient_id)
        )
        ''')

        # Create tags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        ''')

        # Create recipe_tags junction table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_tags (
            recipe_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (recipe_id, tag_id)
        )
        ''')

        # Create shopping_list table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
        )
        ''')

        # Create recipe_reviews table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
        ''')

        # Create ingredient_inventory_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_inventory_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER,
            action_type TEXT,
            quantity_change REAL,
            new_quantity REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
        )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)')

        conn.commit()
        conn.close()

    def insert_sample_data(self):
        """Inserts sample data into the database for testing."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Sample tags
        sample_tags = [
            ('breakfast',),
            ('lunch',),
            ('dinner',),
            ('dessert',),
            ('vegetarian',),
            ('vegan',),
            ('gluten-free',),
            ('quick-meal',),
            ('spicy',),
            ('sweet',),
            ('healthy',),
        ]
        cursor.executemany('INSERT OR IGNORE INTO tags (name) VALUES (?)', sample_tags)

        # Sample ingredients
        sample_ingredients = [
            ('Rice', 'Grains', 1000, 'g', '2025-12-31'),
            ('Chicken', 'Meat', 500, 'g', '2024-12-25'),
            ('Tomato', 'Vegetables', 300, 'g', '2024-12-23'),
            ('Salt', 'Spices', 200, 'g', '2025-06-30'),
            ('Sugar', 'Baking', 500, 'g', '2025-12-31'),
        ]
        cursor.executemany('''
        INSERT OR IGNORE INTO ingredients (name, category, quantity, unit, expiry_date)
        VALUES (?, ?, ?, ?, ?)
        ''', sample_ingredients)

        # Sample recipe
        cursor.execute('''
        INSERT OR IGNORE INTO recipes 
        (name, cuisine_type, preparation_time, difficulty_level, taste_profile, instructions, servings, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Chicken Rice', 'Asian', 45, 'Medium', 'Savory', 
              '1. Cook rice\n2. Season chicken\n3. Cook chicken\n4. Serve together', 4, 4.5))

        conn.commit()
        conn.close()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_database()
    db_manager.insert_sample_data()
    print("Database created successfully!")