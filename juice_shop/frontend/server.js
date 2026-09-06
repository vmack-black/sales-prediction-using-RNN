/**
 * Juice Shop - Node.js Frontend Server
 * Express server serving customer & manager portals.
 * Communicates with the Python Flask backend API.
 */
const express = require("express");
const axios = require("axios");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:5000";

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Simple session via cookie
app.use((req, res, next) => {
    const cookie = req.headers.cookie || "";
    const userCookie = cookie.split(";").map(c => c.trim()).find(c => c.startsWith("juice_user="));
    if (userCookie) {
        try {
            res.locals.user = JSON.parse(decodeURIComponent(userCookie.split("=")[1]));
        } catch {
            res.locals.user = null;
        }
    } else {
        res.locals.user = null;
    }
    next();
});

function requireAuth(req, res, next) {
    if (!res.locals.user) return res.redirect("/login");
    next();
}

function requireRole(role) {
    return (req, res, next) => {
        if (!res.locals.user) return res.redirect("/login");
        if (res.locals.user.role !== role) return res.redirect("/login");
        next();
    };
}

// Helper to call backend API
async function api(method, endpoint, data = null) {
    try {
        const config = { method, url: `${BACKEND_URL}${endpoint}`, timeout: 15000 };
        if (data && (method === "POST" || method === "PUT")) {
            config.data = data;
            config.headers = { "Content-Type": "application/json" };
        }
        const resp = await axios(config);
        return resp.data;
    } catch (err) {
        console.error(`API Error [${method} ${endpoint}]:`, err.message);
        if (err.response) return err.response.data;
        return { error: err.message };
    }
}

// ============================================================
// AUTH PAGES
// ============================================================
app.get("/", (req, res) => {
    if (res.locals.user) {
        return res.redirect(res.locals.user.role === "manager" ? "/manager/dashboard" : "/customer/shop");
    }
    res.render("landing", { user: null });
});

app.get("/login", (req, res) => {
    res.render("login", { user: null, error: null });
});

app.post("/login", async (req, res) => {
    const { username, password } = req.body;
    const result = await api("POST", "/api/login", { username, password });
    if (result.success) {
        res.setHeader("Set-Cookie", `juice_user=${encodeURIComponent(JSON.stringify(result.user))}; Path=/; Max-Age=86400`);
        return res.redirect(result.user.role === "manager" ? "/manager/dashboard" : "/customer/shop");
    }
    res.render("login", { user: null, error: result.message || "Login failed" });
});

app.get("/register", (req, res) => {
    res.render("register", { user: null, error: null });
});

app.post("/register", async (req, res) => {
    const { username, password, full_name, email } = req.body;
    const result = await api("POST", "/api/register", { username, password, full_name, email, role: "customer" });
    if (result.success) {
        res.setHeader("Set-Cookie", `juice_user=${encodeURIComponent(JSON.stringify(result.user))}; Path=/; Max-Age=86400`);
        return res.redirect("/customer/shop");
    }
    res.render("register", { user: null, error: result.message || "Registration failed" });
});

app.get("/logout", (req, res) => {
    res.setHeader("Set-Cookie", "juice_user=; Path=/; Max-Age=0");
    res.redirect("/login");
});

// ============================================================
// CUSTOMER PAGES
// ============================================================
app.get("/customer/shop", requireRole("customer"), async (req, res) => {
    const products = await api("GET", "/api/products");
    res.render("customer/shop", { user: res.locals.user, products });
});

app.get("/customer/product/:id", requireRole("customer"), async (req, res) => {
    const product = await api("GET", `/api/products/${req.params.id}`);
    res.render("customer/product", { user: res.locals.user, product });
});

app.post("/customer/order", requireRole("customer"), async (req, res) => {
    const { items } = req.body;
    const result = await api("POST", "/api/orders", { user_id: res.locals.user.id, items: JSON.parse(items) });
    res.json(result);
});

app.get("/customer/orders", requireRole("customer"), async (req, res) => {
    const orders = await api("GET", `/api/orders/${res.locals.user.id}`);
    res.render("customer/orders", { user: res.locals.user, orders });
});

app.post("/customer/review", requireRole("customer"), async (req, res) => {
    const { product_id, rating, comment } = req.body;
    const result = await api("POST", "/api/reviews", {
        product_id: parseInt(product_id), user_id: res.locals.user.id,
        rating: parseInt(rating), comment
    });
    res.json(result);
});

app.get("/customer/reviews", requireRole("customer"), async (req, res) => {
    const products = await api("GET", "/api/products");
    // get reviews for each product with reviews
    res.render("customer/reviews", { user: res.locals.user, products });
});

app.get("/customer/profile", requireRole("customer"), (req, res) => {
    res.render("customer/profile", { user: res.locals.user });
});

// ============================================================
// MANAGER PAGES
// ============================================================
app.get("/manager/dashboard", requireRole("manager"), async (req, res) => {
    const stats = await api("GET", "/api/dashboard");
    res.render("manager/dashboard", { user: res.locals.user, stats });
});

app.get("/manager/inventory", requireRole("manager"), async (req, res) => {
    const inventory = await api("GET", "/api/inventory");
    res.render("manager/inventory", { user: res.locals.user, inventory });
});

app.post("/manager/restock/:id", requireRole("manager"), async (req, res) => {
    const amount = parseInt(req.body.amount);
    const result = await api("PUT", `/api/inventory/${req.params.id}/restock`, { amount });
    res.json(result);
});

app.get("/manager/alerts", requireRole("manager"), async (req, res) => {
    const alerts = await api("GET", "/api/alerts");
    res.render("manager/alerts", { user: res.locals.user, alerts });
});

app.post("/manager/alerts/check", requireRole("manager"), async (req, res) => {
    const result = await api("POST", "/api/alerts/check");
    res.json(result);
});

app.post("/manager/alerts/:id/resolve", requireRole("manager"), async (req, res) => {
    const result = await api("PUT", `/api/alerts/${req.params.id}/resolve`);
    res.json(result);
});

app.get("/manager/predictions", requireRole("manager"), async (req, res) => {
    const days = req.query.days || 7;
    const predictions = await api("GET", `/api/predict/sales?days=${days}`);
    const salesHistory = await api("GET", "/api/sales/history?days=30");
    const modelInfo = await api("GET", "/api/predict/info");
    res.render("manager/predictions", { user: res.locals.user, predictions, salesHistory, modelInfo, days: parseInt(days) });
});

app.post("/manager/predictions", requireRole("manager"), async (req, res) => {
    const days = parseInt(req.body.days) || 7;
    res.redirect(`/manager/predictions?days=${days}`);
});

app.get("/manager/sales", requireRole("manager"), async (req, res) => {
    const history = await api("GET", "/api/sales/history?days=30");
    res.render("manager/sales", { user: res.locals.user, history });
});

// ============================================================
// API PROXY (for frontend JS fetch calls)
// ============================================================
app.get("/api/products", async (req, res) => {
    res.json(await api("GET", "/api/products"));
});
app.get("/api/dashboard", async (req, res) => {
    res.json(await api("GET", "/api/dashboard"));
});
app.get("/api/inventory", async (req, res) => {
    res.json(await api("GET", "/api/inventory"));
});
app.get("/api/alerts", async (req, res) => {
    res.json(await api("GET", "/api/alerts"));
});

// ============================================================
app.listen(PORT, () => {
    console.log(`🥤 Juice Shop Frontend running on http://localhost:${PORT}`);
    console.log(`   Backend API: ${BACKEND_URL}`);
    console.log(`   Default users: customer/customer123 | manager/manager123`);
});
