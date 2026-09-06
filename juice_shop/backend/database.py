"""
Juice Shop - Database Module
SQLite database with all tables for products, users, orders, reviews, inventory, alerts.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "juice_shop.db")

def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize the database with all tables and seed data."""
    conn = get_db()
    c = conn.cursor()

    # ---------------- USERS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('customer','manager')),
        full_name TEXT,
        email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- PRODUCTS (20 items) ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        size_ml INTEGER DEFAULT 250,
        calories INTEGER DEFAULT 0,
        stock INTEGER DEFAULT 50,
        low_stock_threshold INTEGER DEFAULT 10,
        image TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- ORDERS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # ---------------- ORDER ITEMS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # ---------------- REVIEWS & RATINGS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # ---------------- INVENTORY LOG ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        change_amount INTEGER NOT NULL,
        reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # ---------------- ALERTS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        severity TEXT DEFAULT 'info',
        product_id INTEGER,
        resolved INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # ---------------- SALES HISTORY (for RNN prediction) ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        quantity_sold INTEGER NOT NULL,
        revenue REAL NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()

    # Seed default users if not exists
    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()["cnt"] == 0:
        c.execute("INSERT INTO users (username, password, role, full_name, email) VALUES (?,?,?,?,?)",
                  ("customer", "customer123", "customer", "Demo Customer", "customer@juiceshop.com"))
        c.execute("INSERT INTO users (username, password, role, full_name, email) VALUES (?,?,?,?,?)",
                  ("manager", "manager123", "manager", "Shop Manager", "manager@juiceshop.com"))
        print("[DB] Seeded 2 default users")

    # Seed products if not exists
    c.execute("SELECT COUNT(*) as cnt FROM products")
    if c.fetchone()["cnt"] == 0:
        products = [
            ("Orange Burst", "Citrus", "Freshly squeezed oranges with a zesty kick.", 4.50, 250, 110, 80, 15),
            ("Mango Tango", "Tropical", "Ripe mangoes blended into a smooth tropical delight.", 5.25, 300, 130, 65, 15),
            ("Green Detox", "Detox", "Spinach, cucumber, apple, and celery cleansing blend.", 6.00, 350, 90, 45, 12),
            ("Berry Blast", "Berry", "Mixed berries - strawberry, blueberry, and raspberry.", 5.75, 300, 120, 70, 15),
            ("Watermelon Wave", "Hydration", "Refreshing watermelon juice with mint.", 4.25, 350, 80, 90, 20),
            ("Pineapple Paradise", "Tropical", "Sweet pineapple with a hint of coconut.", 5.50, 300, 125, 55, 15),
            ("Carrot Glow", "Veggie", "Carrot and orange for healthy skin and immunity.", 4.75, 250, 95, 40, 12),
            ("Beet Boost", "Veggie", "Beetroot, apple, and ginger energy booster.", 5.95, 300, 105, 35, 12),
            ("Apple Crisp", "Fruit", "Pure pressed apple juice, naturally sweet.", 3.95, 250, 115, 100, 15),
            ("Pomegranate Power", "Antioxidant", "Rich pomegranate juice loaded with antioxidants.", 6.50, 250, 135, 30, 10),
            ("Cucumber Cooler", "Hydration", "Cucumber, lime, and mint for ultimate refreshment.", 4.00, 350, 50, 85, 20),
            ("Strawberry Sunrise", "Berry", "Sweet strawberries with a touch of banana.", 5.25, 300, 140, 60, 15),
            ("Lemon Zest", "Citrus", "Tangy lemonade with honey and ginger.", 3.75, 300, 70, 95, 15),
            ("Avocado Cream", "Creamy", "Creamy avocado and spinach superfood smoothie.", 7.25, 350, 180, 25, 10),
            ("Peach Perfection", "Fruit", "Ripe peaches blended into a silky smooth juice.", 5.00, 300, 120, 50, 12),
            ("Kiwi Kick", "Fruit", "Kiwi and apple with a tangy twist.", 4.85, 250, 100, 45, 12),
            ("Coconut Bliss", "Tropical", "Pure coconut water with tropical fruit essence.", 4.50, 350, 60, 75, 15),
            ("Cherry Charm", "Berry", "Sweet dark cherry juice rich in flavor.", 6.25, 250, 130, 20, 10),
            ("Grape Galaxy", "Fruit", "Concord grape juice, bold and naturally sweet.", 4.25, 250, 125, 65, 15),
            ("Ginger Fire", "Wellness", "Ginger, lemon, and turmeric immunity shot.", 5.50, 150, 40, 15, 8),
        ]
        for p in products:
            name, cat, desc, price, size, cal, stock, threshold = p
            c.execute("""INSERT INTO products (name, category, description, price, size_ml, calories, stock, low_stock_threshold)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (name, cat, desc, price, size, cal, stock, threshold))
        print(f"[DB] Seeded {len(products)} products")

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully")

if __name__ == "__main__":
    init_db()
