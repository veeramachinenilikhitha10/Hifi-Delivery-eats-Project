import sqlite3
from datetime import datetime

def create_tables(cursor):
    # Create Category Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Category (
        CategoryID INTEGER PRIMARY KEY,
        CategoryName TEXT NOT NULL,
        Description TEXT,
        CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create Dietary Preferences Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DietaryPreferences (
        PreferenceID INTEGER PRIMARY KEY,
        PreferenceName TEXT NOT NULL,
        Description TEXT,
        CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create Menu Items Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MenuItems (
        MenuItemID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Description TEXT,
        Price DECIMAL(10, 2) NOT NULL,
        CategoryID INTEGER,
        AvailabilityStatus BOOLEAN DEFAULT 1,
        ImageURL TEXT,
        CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        ModifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
    )
    ''')

    # Create Menu Item Dietary Preferences (Junction Table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MenuItemDietaryPreferences (
        MenuItemID INTEGER,
        PreferenceID INTEGER,
        PRIMARY KEY (MenuItemID, PreferenceID),
        FOREIGN KEY (MenuItemID) REFERENCES MenuItems(MenuItemID),
        FOREIGN KEY (PreferenceID) REFERENCES DietaryPreferences(PreferenceID)
    )
    ''')

def insert_sample_data(cursor):
    # Insert sample categories
    categories = [
        ("Main Course", "Primary dish of a meal"),
        ("Appetizer", "Small dish served before the main course"),
        ("Dessert", "Sweet course at the end of a meal"),
        ("Beverage", "Drinks to accompany the meal")
    ]
    cursor.executemany("INSERT INTO Category (CategoryName, Description) VALUES (?, ?)", categories)

    # Insert sample dietary preferences
    preferences = [
        ("Vegetarian", "No meat, may include dairy and eggs"),
        ("Vegan", "No animal products"),
        ("Gluten-Free", "No gluten-containing ingredients"),
        ("Nut-Free", "No nuts or nut-derived ingredients")
    ]
    cursor.executemany("INSERT INTO DietaryPreferences (PreferenceName, Description) VALUES (?, ?)", preferences)

    # Insert sample menu items
    menu_items = [
        ("Margherita Pizza", "Classic pizza with tomato, mozzarella, and basil", 12.99, 1, 1, "/static/images/margherita.jpg"),
        ("Caesar Salad", "Romaine lettuce with Caesar dressing and croutons", 8.99, 2, 1, "/static/images/caesar_salad.jpg"),
        ("Chocolate Lava Cake", "Warm chocolate cake with a gooey center", 6.99, 3, 1, "/static/images/lava_cake.jpg"),
        ("Iced Tea", "Freshly brewed and chilled black tea", 2.99, 4, 1, "/static/images/iced_tea.jpg")
    ]
    cursor.executemany("INSERT INTO MenuItems (Name, Description, Price, CategoryID, AvailabilityStatus, ImageURL) VALUES (?, ?, ?, ?, ?, ?)", menu_items)

    # Insert sample menu item dietary preferences
    item_preferences = [
        (1, 1),  # Margherita Pizza is Vegetarian
        (2, 1),  # Caesar Salad is Vegetarian
        (3, 3),  # Chocolate Lava Cake is Gluten-Free
        (4, 2)   # Iced Tea is Vegan
    ]
    cursor.executemany("INSERT INTO MenuItemDietaryPreferences (MenuItemID, PreferenceID) VALUES (?, ?)", item_preferences)

# Connect to the database (this will create it if it doesn't exist)
conn = sqlite3.connect('enhanced_menu_management.db')
cursor = conn.cursor()

# Create tables
create_tables(cursor)

# Insert sample data
insert_sample_data(cursor)

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database setup complete with sample data.")