# Juice Shop Project - Task Plan

## Project Overview
- **Frontend**: Node.js (Express + EJS templates + CSS)
- **Backend**: Python (Flask REST API)
- **ML**: RNN (LSTM/TensorFlow) for sales prediction
- **Users**: Customer & Manager roles
- **Products**: 20 juice shop items

## Tasks

### Phase 1: Project Structure & Setup
- [x] Create project directory structure
- [x] Create todo.md
- [x] Define product catalog (20 items)
- [x] Set up database schema

### Phase 2: Python Backend (Flask)
- [x] Create Flask app structure
- [x] Implement product endpoints
- [x] Implement authentication (customer/manager)
- [x] Implement customer features (orders, reviews, ratings)
- [x] Implement manager features (inventory, alerts, dashboard)
- [x] Integrate RNN prediction endpoint
- [x] Create seed data script

### Phase 3: RNN Model (Sales Prediction)
- [x] Create RNN model with TensorFlow/Keras (LSTM)
- [x] Generate synthetic sales data with seasonality
- [x] Train the model (100 epochs)
- [x] Create prediction API module
- [x] Save trained model (sales_rnn_model.h5)

### Phase 4: Node.js Frontend
- [x] Create Express app + server.js
- [x] Build customer pages (shop, product detail, cart, orders, reviews, profile)
- [x] Build manager pages (dashboard, inventory, alerts, predictions, sales)
- [x] Style with custom CSS (modern, responsive design)
- [x] Connect frontend to Python backend (Axios)
- [x] Fix EJS include paths

### Phase 5: Testing & Documentation
- [x] Create startup script (start.sh)
- [x] Test backend API endpoints (login, products, orders, reviews, predictions)
- [x] Test frontend pages (customer + manager)
- [x] Visual verification via browser screenshots
- [x] Write README documentation
- [x] Final delivery
