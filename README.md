

# 🚀 Crypto Investment Manager

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

> **A full-stack, data-driven cryptocurrency analytics platform featuring automated ETL pipelines and machine learning price forecasting.**

**Crypto Investment Manager** is an end-to-end Python web application engineered to democratize cryptocurrency analysis. By programmatically ingesting market data and applying predictive statistical models, the platform acts as an automated financial advisor. It calculates dynamic price forecasts, optimal investment spreads, risk classifications, and expected return timelines (ETAs) for major assets like Bitcoin, Ethereum, and Binance Coin. 

Designed with a modular architecture, the system abstracts complex backend data processing into an intuitive, interactive web dashboard.

---

## ✨ System Features

### 💻 System & Security
* **Secure Authentication Pipeline:** Fully authenticated user sessions managed via `Flask-Login` and backed by a local `SQLite` relational database.
* **Modular Execution Engine:** Dynamically orchestrates heavy analytical Python scripts via `subprocess` routing, separating web serving from data processing.

### 📊 Data Engineering & Analytics
* **Automated Data Ingestion:** Integrates seamlessly with the CoinGecko API to pull continuous historical market data without relying on paid API keys.
* **Robust Data Processing:** Utilizes `pandas` to clean, transform, and feature-engineer raw JSON payloads into structured, analysis-ready CSV datasets.
* **Risk & ETA Modeling:** Algorithmically evaluates current market momentum against historical averages to classify asset risk and project realistic timelines for target returns.
* **Smart Portfolio Mixer:** Computes optimal cryptocurrency combinations to project blended portfolio returns across different asset distributions.

### 🧠 Machine Learning Engine
* **Predictive Price Forecasting:** Implements `scikit-learn` Linear Regression models to evaluate historical trendlines and forecast future asset valuations over user-defined time horizons (e.g., 30-day windows).

### 🖥️ User Interface & Reporting
* **Interactive Data Visualization:** Renders complex statistical outputs directly to the frontend using highly responsive `Chart.js` graphs natively bound to backend data models via Jinja2.
* **Automated Report Generation:** Compiles analytical findings into downloadable structured text reports and CSV grids for offline review.

---

## 🏗️ Architecture & Workflow

The platform follows a clean **ETL (Extract, Transform, Load) → Inference → Presentation** architecture:

1. **Extract (data_collection.py):** Automatically fetches up to 365 days of raw historical market data.
2. **Transform (`data_processing.py`):** Cleans timestamps, handles missing values, and engineers continuous numerical features for model training.
3. **Inference (price_forecast.py / risk_checker.py):** Trains statistical models on the processed data to generate predictive metrics, saving outputs locally to the `/data/processed/` pipeline.
4. **Presentation (app.py / `templates/`):** The Flask controller reads the generated insights, contextualizes them, and serves them to the client interface for dynamic visualization.

---

## 🛠️ Technical Stack

* **Backend Framework:** Python 3.8+, Flask, Flask-Login
* **Data Science & ML:** Pandas, NumPy, Scikit-Learn (`LinearRegression`)
* **Database & ORM:** SQLite, SQLAlchemy
* **External APIs:** Requests (CoinGecko REST API)
* **Frontend:** HTML5, CSS3, Jinja2 Templating, Chart.js

---

## ⚙️ Quick Start Guide

### Prerequisites
* Python 3.8 or higher installed on your local machine.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/crypto_investment_manager.git
cd crypto_investment_manager

# 2. Create and activate a virtual environment (Recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install required application dependencies
pip install Flask Flask-Login Flask-SQLAlchemy pandas numpy scikit-learn requests
```

### Execution

To launch the local development server:
```bash
python app.py
```
*Navigate to `http://127.0.0.1:5000/` in your browser. Register a new user account to unlock the dashboard and trigger your first data analysis.*

---

## 📂 Repository Structure

```text
crypto_investment_manager/
├── app.py                         # Application factory & server initialization
├── *_routes.py                    # Modularized Flask blueprints (auth, dashboard, analysis)
├── data_collection.py             # API Integration (ETL: Extract)
├── data_processing.py             # Feature engineering & formatting (ETL: Transform)
├── price_forecast.py              # ML execution script (Scikit-Learn)
├── risk_checker.py                # Asset risk classification logic
├── investment_mix_calculator.py   # Portfolio distribution modeling
├── returns_eta.py                 # Algorithmic time projection
├── models.py                      # SQLAlchemy schemas & Data I/O utilities
├── data/                          # Isolated data environment (raw, processed, DBs, reports)
├── static/                        # Static UI assets (CSS, Chart.js logic)
└── templates/                     # MVC Views: Jinja2-powered HTML components
```

---

## 🔮 Future Roadmap

Highlighting self-awareness and architectural growth potential:

- **Algorithm Upgrades:** Transition from basic Linear Regression to advanced time-series models like **ARIMA** or **LSTM neural networks** for enhanced accuracy in volatile markets.
- **Asynchronous Task Queues:** Replace synchronous Flask `subprocess` calls with **Celery and Redis** to handle large-scale data processing in the background, minimizing HTTP request bottlenecks.
- **Real-Time Data Streaming:** Implement **WebSockets** for live, tick-by-tick portfolio updates rather than relying solely on daily aggregate limits.
- **Containerization:** Add a **Dockerfile** and `docker-compose.yml` for seamless, one-click environment deployment.

---

## 📜 License & Compliance

Developed for educational and portfolio demonstration purposes. All historical market data is sourced responsibly via the [CoinGecko API free-tier](https://www.coingecko.com/en/api/pricing). Ensure compliance with rate limits during further development.
