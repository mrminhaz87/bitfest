import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name='kitchen_inventory.db'):
        self.db_name = db_name
        
    def create_database(self):
        """Creates SQLite database for kitchen inventory management."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create ingredients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity REAL DEFAULT 0,
            unit TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create inventory_history table for tracking changes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER,
            action_type TEXT,  -- 'add', 'remove', 'update'
            quantity_change REAL,
            new_quantity REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
        )
        ''')

        # Create index for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name)')

        conn.commit()
        conn.close()

    def insert_sample_data(self):
        """Insert sample ingredients for testing."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Sample ingredients
        sample_ingredients = [
            ('Rice', 1000, 'g'),
            ('Chicken', 500, 'g'),
            ('Tomato', 300, 'g'),
            ('Salt', 200, 'g'),
            ('Milk', 1000, 'ml'),
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO ingredients 
        (name, quantity, unit)
        VALUES (?, ?, ?)
        ''', sample_ingredients)

        conn.commit()
        conn.close()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_database()
    db_manager.insert_sample_data()
    print("Database created successfully with sample data!")