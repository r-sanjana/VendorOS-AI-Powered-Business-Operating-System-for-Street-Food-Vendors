# VendorOS – AI-Powered Business Operating System for Street Food Vendors(Ongoing)

🚀 A production-grade SaaS backend platform designed to help street food vendors digitize and optimize their business operations using inventory management, sales tracking, expense analytics, business intelligence dashboards, and AI-powered forecasting.

---

## 🌟 Project Overview

VendorOS is an AI-powered business management platform built specifically for street food vendors and small food businesses.

The platform enables vendors to:

- Manage business and vendor profiles
- Track inventory and stock movements
- Record and analyze sales transactions
- Monitor expenses and profitability
- View real-time business KPIs
- Receive AI-powered demand forecasts
- Get intelligent business recommendations

---

## 🔗 Live Deployment

### Backend API

https://vendoros-backend.onrender.com/api/docs

### Health Check

https://vendoros-backend.onrender.com/health

---

## ✨ Features

### 🔐 Authentication & Security

- JWT Authentication
- Access & Refresh Tokens
- Password Hashing using bcrypt
- Role-Based Access Control (RBAC)
- Protected API Routes
- Token Validation

### 🏪 Vendor Management

- Create Vendor Profiles
- View Vendor Details
- Update Vendor Information
- Delete Vendors
- Pagination Support

### 📦 Inventory Management

- Inventory CRUD Operations
- Stock Quantity Tracking
- Stock Movement Management
- Low Stock Monitoring
- Inventory Analytics

### 💰 Sales Management

- Record Sales Transactions
- Revenue Tracking
- Sales Analytics
- Product Performance Analysis
- Revenue Trend Monitoring

### 🧾 Expense Management

- Expense CRUD Operations
- Expense Categorization
- Expense Analytics
- Profitability Tracking
- Cost Monitoring

### 📊 Dashboard Analytics

- Total Revenue
- Total Expenses
- Net Profit
- Inventory Insights
- Low Stock Alerts
- Business Performance KPIs

### 🤖 Artificial Intelligence Module

#### Demand Forecasting

- Inventory Demand Prediction
- Multi-Day Forecasting
- Confidence Scoring

#### Sales Prediction

- Daily Revenue Forecasting
- Weekly Revenue Prediction
- Confidence Intervals

#### Recommendation Engine

- Revenue Optimization Suggestions
- Inventory Recommendations
- Expense Reduction Insights
- Business Health Analysis

---

## 🛠 Tech Stack

### Backend

- FastAPI
- Python 3.10
- SQLAlchemy 2.0
- Pydantic v2
- Uvicorn

### Database

- PostgreSQL
- AsyncPG
- Alembic Migrations

### Authentication

- JWT
- Python-Jose
- Passlib
- bcrypt

### AI / Machine Learning

- Scikit-Learn
- NumPy
- Pandas
- SciPy

### Testing

- Pytest
- Pytest-Asyncio
- HTTPX

### DevOps

- Git
- GitHub
- GitHub Actions
- Render

---

## 🏗 System Architecture

```text
User
  │
  ▼
Frontend (Planned)
  │
  ▼
FastAPI Backend (VendorOS)
  │
  ▼
PostgreSQL Database
  │
  ▼
AI Analytics & Forecasting Engine
```

---

## 📂 Project Structure

```text
VendorOS
│
├── app
│   ├── ai
│   ├── core
│   ├── database
│   ├── models
│   ├── routes
│   ├── schemas
│   ├── services
│   └── utils
│
├── migrations
│
├── tests
│
├── requirements.txt
├── runtime.txt
├── alembic.ini
└── README.md
```

---

## 🧪 Testing

VendorOS includes a comprehensive automated testing suite.

### Test Modules

- Authentication Tests
- Vendor Tests
- Inventory Tests
- Sales Tests
- Expense Tests
- Security Tests
- AI Module Tests

### Latest Test Results

```text
77 Passed
0 Failed
0 Errors
```

GitHub Actions automatically runs all tests on every push and pull request.

---

## ⚙️ CI/CD Pipeline

VendorOS uses GitHub Actions for Continuous Integration.

### Workflow

```text
Code Push
   │
   ▼
GitHub Actions
   │
   ▼
Install Dependencies
   │
   ▼
Run Automated Tests
   │
   ▼
77 Tests Passed
   │
   ▼
Deployment Ready
```

### Benefits

- Automated Testing
- Continuous Validation
- Quality Assurance
- Regression Prevention

---

## ☁️ Cloud Infrastructure

### Backend Hosting

- Render Web Service

### Database Hosting

- Render PostgreSQL

### Source Control

- GitHub Repository

### Continuous Integration

- GitHub Actions

---

## 🔒 Security Features

- JWT Authentication
- Password Hashing (bcrypt)
- Role-Based Authorization
- Input Validation
- Secure Database Access
- Protected API Endpoints

---

## 📈 Current Project Status

| Module | Status |
|----------|----------|
| Authentication System | ✅ Complete |
| Vendor Management | ✅ Complete |
| Inventory Management | ✅ Complete |
| Sales Management | ✅ Complete |
| Expense Management | ✅ Complete |
| Dashboard Analytics | ✅ Complete |
| AI Forecasting | ✅ Complete |
| Recommendation Engine | ✅ Complete |
| PostgreSQL Integration | ✅ Complete |
| Automated Testing | ✅ Complete |
| GitHub Actions CI/CD | ✅ Complete |
| Cloud Deployment | ✅ Complete |
| API Documentation | ✅ Complete |
| Frontend Development | 🟡 In Progress |

---

## 📊 Project Maturity

| Area | Completion |
|---------|------------|
| Backend Development | 100% |
| Database Design | 95% |
| Testing Coverage | 95% |
| CI/CD Pipeline | 95% |
| Deployment | 95% |
| Security | 90% |
| AI Features | 85% |
| Documentation | 90% |
| Frontend | 20% |

---

## ⭐ Key Achievements

- ✅ Production Deployment on Render
- ✅ PostgreSQL Cloud Database
- ✅ AI-Powered Forecasting Engine
- ✅ Automated Testing Suite
- ✅ 77 Passing Tests
- ✅ GitHub Actions CI/CD Pipeline
- ✅ Interactive API Documentation
- ✅ Scalable SaaS Architecture
- ✅ Cloud-Native Infrastructure

---

## 👩‍💻 Developer

**Sanjana R**

Artificial Intelligence and Machine Learning Engineering Student

### Project

**VendorOS – AI-Powered Business Operating System for Street Food Vendors**

A production-grade backend platform built using modern software engineering practices, machine learning, automated testing, CI/CD, PostgreSQL, and cloud deployment.

---
