"""
Juice Shop - Flask Backend API
Handles authentication, products, orders, reviews, inventory, alerts, and predictions.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, init_db
import datetime
import os
import sys

# Add ml_model directory to path for prediction imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_model"))

app = Flask(__name__)
CORS(app)

# ============================================================
# AUTHENTICATION
# ============================================================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    conn.close()
    if user:
        return jsonify({"success": True, "user": {"id": user["id"], "username": user["username"],
                         "role": user["role"], "full_name": user["full_name"], "email": user["email"]}})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "")
    email = data.get("email", "")
    role = data.get("role", "customer")
    if role not in ("customer", "manager"):
        role = "customer"
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO users (username, password, role, full_name, email) VALUES (?,?,?,?,?)",
                           (username, password, role, full_name, email))
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return jsonify({"success": True, "user": {"id": uid, "username": username, "role": role,
                         "full_name": full_name, "email": email}})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": "Username already exists"}), 400

# ============================================================
# PRODUCTS
# ============================================================
@app.route("/api/products", methods=["GET"])
def get_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    result = []
    for p in products:
        avg = conn.execute("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE product_id=?", (p["id"],)).fetchone()
        result.append(dict(p))
        result[-1]["avg_rating"] = round(avg["avg"], 2) if avg["avg"] else 0
        result[-1]["review_count"] = avg["cnt"]
    conn.close()
    return jsonify(result)

@app.route("/api/products/<int:pid>", methods=["GET"])
def get_product(pid):
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    reviews = conn.execute("""SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id=u.id 
                              WHERE r.product_id=? ORDER BY r.created_at DESC""", (pid,)).fetchall()
    result = dict(p)
    avg = conn.execute("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE product_id=?", (pid,)).fetchone()
    result["avg_rating"] = round(avg["avg"], 2) if avg["avg"] else 0
    result["review_count"] = avg["cnt"]
    result["reviews"] = [dict(r) for r in reviews]
    conn.close()
    return jsonify(result)

# ============================================================
# ORDERS (CUSTOMER)
# ============================================================
@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    items = data.get("items", [])
    if not items:
        return jsonify({"success": False, "message": "Cart is empty"}), 400
    conn = get_db()
    total = 0
    order_items = []
    for it in items:
        pid = it["product_id"]
        qty = it["quantity"]
        prod = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if not prod:
            conn.close()
            return jsonify({"success": False, "message": f"Product {pid} not found"}), 400
        if prod["stock"] < qty:
            conn.close()
            return jsonify({"success": False, "message": f"Insufficient stock for {prod['name']}"}), 400
        line_total = prod["price"] * qty
        total += line_total
        order_items.append((pid, qty, prod["price"], line_total, prod["name"]))
    cur = conn.execute("INSERT INTO orders (user_id, total, status) VALUES (?,?,?)", (user_id, total, "pending"))
    order_id = cur.lastrowid
    for pid, qty, price, line_total, pname in order_items:
        conn.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)",
                     (order_id, pid, qty, price))
        conn.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))
        conn.execute("INSERT INTO inventory_log (product_id, change_amount, reason) VALUES (?,?,?)",
                     (pid, -qty, f"Order #{order_id}"))
    # Record sales history for prediction
    today = datetime.date.today().isoformat()
    for pid, qty, price, line_total, pname in order_items:
        conn.execute("INSERT INTO sales_history (product_id, date, quantity_sold, revenue) VALUES (?,?,?,?)",
                     (pid, today, qty, line_total))
    # Check low stock alerts
    for pid, qty, price, line_total, pname in order_items:
        prod = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if prod["stock"] <= prod["low_stock_threshold"]:
            conn.execute("INSERT INTO alerts (type, message, severity, product_id) VALUES (?,?,?,?)",
                         ("low_stock", f"Low stock alert: {prod['name']} has only {prod['stock']} units left", "warning", pid))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "order_id": order_id, "total": round(total, 2),
                    "message": "Order placed successfully"})

@app.route("/api/orders/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
    result = []
    for o in orders:
        items = conn.execute("""SELECT oi.*, p.name as product_name, p.category 
                                FROM order_items oi JOIN products p ON oi.product_id=p.id 
                                WHERE oi.order_id=?""", (o["id"],)).fetchall()
        d = dict(o)
        d["items"] = [dict(i) for i in items]
        result.append(d)
    conn.close()
    return jsonify(result)

@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.json
    status = data.get("status")
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Status updated"})

# ============================================================
# REVIEWS & RATINGS (CUSTOMER)
# ============================================================
@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.json
    product_id = data.get("product_id")
    user_id = data.get("user_id")
    rating = data.get("rating")
    comment = data.get("comment", "")
    if not (1 <= rating <= 5):
        return jsonify({"success": False, "message": "Rating must be 1-5"}), 400
    conn = get_db()
    # Prevent duplicate review per user per product (update instead)
    existing = conn.execute("SELECT * FROM reviews WHERE product_id=? AND user_id=?", (product_id, user_id)).fetchone()
    if existing:
        conn.execute("UPDATE reviews SET rating=?, comment=? WHERE id=?", (rating, comment, existing["id"]))
    else:
        conn.execute("INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?,?,?,?)",
                     (product_id, user_id, rating, comment))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Review submitted"})

@app.route("/api/products/<int:pid>/reviews", methods=["GET"])
def get_product_reviews(pid):
    conn = get_db()
    reviews = conn.execute("""SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id=u.id 
                              WHERE r.product_id=? ORDER BY r.created_at DESC""", (pid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in reviews])

# ============================================================
# MANAGER: INVENTORY
# ============================================================
@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    result = []
    for p in products:
        d = dict(p)
        d["status"] = "critical" if p["stock"] <= p["low_stock_threshold"]//2 else ("low" if p["stock"] <= p["low_stock_threshold"] else "ok")
        result.append(d)
    conn.close()
    return jsonify(result)

@app.route("/api/inventory/<int:pid>/restock", methods=["PUT"])
def restock(pid):
    data = request.json
    amount = data.get("amount", 0)
    conn = get_db()
    conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (amount, pid))
    conn.execute("INSERT INTO inventory_log (product_id, change_amount, reason) VALUES (?,?,?)",
                 (pid, amount, "Manager restock"))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Restocked {amount} units"})

# ============================================================
# MANAGER: ALERTS
# ============================================================
@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    conn = get_db()
    alerts = conn.execute("SELECT a.*, p.name as product_name FROM alerts a LEFT JOIN products p ON a.product_id=p.id WHERE a.resolved=0 ORDER BY a.created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(a) for a in alerts])

@app.route("/api/alerts/<int:aid>/resolve", methods=["PUT"])
def resolve_alert(aid):
    conn = get_db()
    conn.execute("UPDATE alerts SET resolved=1 WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Alert resolved"})

# Auto-generate low-stock alerts
@app.route("/api/alerts/check", methods=["POST"])
def check_alerts():
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    count = 0
    for p in products:
        if p["stock"] <= p["low_stock_threshold"]:
            existing = conn.execute("SELECT * FROM alerts WHERE product_id=? AND type='low_stock' AND resolved=0", (p["id"],)).fetchone()
            if not existing:
                sev = "critical" if p["stock"] <= p["low_stock_threshold"]//2 else "warning"
                conn.execute("INSERT INTO alerts (type, message, severity, product_id) VALUES (?,?,?,?)",
                             ("low_stock", f"Low stock: {p['name']} has {p['stock']} units left (threshold: {p['low_stock_threshold']})", sev, p["id"]))
                count += 1
    conn.commit()
    conn.close()
    return jsonify({"success": True, "new_alerts": count})

# ============================================================
# MANAGER: DASHBOARD STATS
# ============================================================
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    conn = get_db()
    total_products = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    total_orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
    total_revenue = conn.execute("SELECT COALESCE(SUM(total),0) as s FROM orders").fetchone()["s"]
    total_customers = conn.execute("SELECT COUNT(*) as c FROM users WHERE role='customer'").fetchone()["c"]
    low_stock = conn.execute("SELECT COUNT(*) as c FROM products WHERE stock <= low_stock_threshold").fetchone()["c"]
    active_alerts = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE resolved=0").fetchone()["c"]
    total_reviews = conn.execute("SELECT COUNT(*) as c FROM reviews").fetchone()["c"]
    avg_rating = conn.execute("SELECT COALESCE(AVG(rating),0) as a FROM reviews").fetchone()["a"]
    # Top products by sales
    top_products = conn.execute("""SELECT p.name, SUM(oi.quantity) as qty, SUM(oi.quantity*oi.price) as rev
                                   FROM order_items oi JOIN products p ON oi.product_id=p.id
                                   GROUP BY p.id ORDER BY qty DESC LIMIT 5""").fetchall()
    # Recent orders
    recent = conn.execute("""SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id=u.id 
                             ORDER BY o.created_at DESC LIMIT 10""").fetchall()
    conn.close()
    return jsonify({
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_customers": total_customers,
        "low_stock_count": low_stock,
        "active_alerts": active_alerts,
        "total_reviews": total_reviews,
        "avg_rating": round(avg_rating, 2),
        "top_products": [dict(t) for t in top_products],
        "recent_orders": [dict(r) for r in recent],
    })

# ============================================================
# SALES HISTORY (for charts & prediction)
# ============================================================
@app.route("/api/sales/history", methods=["GET"])
def sales_history():
    days = request.args.get("days", 30, type=int)
    conn = get_db()
    rows = conn.execute("""SELECT date, SUM(quantity_sold) as qty, SUM(revenue) as rev 
                           FROM sales_history GROUP BY date ORDER BY date DESC LIMIT ?""", (days,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in reversed(rows)])

@app.route("/api/sales/product/<int:pid>/history", methods=["GET"])
def product_sales_history(pid):
    days = request.args.get("days", 30, type=int)
    conn = get_db()
    rows = conn.execute("""SELECT date, quantity_sold, revenue FROM sales_history 
                           WHERE product_id=? ORDER BY date DESC LIMIT ?""", (pid, days)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in reversed(rows)])

# ============================================================
# PREDICTION (RNN) - calls ML model
# ============================================================
@app.route("/api/predict/sales", methods=["GET"])
def predict_sales():
    days = request.args.get("days", 7, type=int)
    try:
        from predict_model import predict_future_sales, get_model_info
        result = predict_future_sales(days)
        return jsonify({"success": True, "predictions": result})
    except Exception as e:
        return jsonify({"success": False, "message": f"Prediction error: {str(e)}"}), 500

@app.route("/api/predict/info", methods=["GET"])
def predict_info():
    try:
        from predict_model import get_model_info
        return jsonify(get_model_info())
    except Exception as e:
        return jsonify({"status": "model not loaded", "error": str(e)})

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    init_db()
    print("Starting Juice Shop Backend on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
