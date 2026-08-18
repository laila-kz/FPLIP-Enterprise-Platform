# 🔎 FPLIP Investigate (Operational Web Application)

**FPLIP Investigate** is the operational web application module of the Factory Performance & Loss Intelligence Platform. Built with Laravel 11, Tailwind CSS, and Vite, it bridges plant floor operations with backend data platform intelligence.

---

## 🎯 Key Capabilities

- **Role-Based Workflows**: Tailored user dashboards for **Plant Managers** and **Technicians**.
- **Automated Anomaly Investigations**: Triggered when OEE drops below 15% or scrap spikes above 20%.
- **AI-Powered Loss Explanations**: Integrates with LLM endpoints (Gemini / DeepSeek) to generate human-readable root-cause explanations.
- **Evidentiary Findings & Photos**: Technicians can capture findings, attach site photos, and submit resolution reports.
- **Complete Audit Trail**: Historical tracking of all raised, assigned, and resolved factory floor anomalies.

---

## 🚀 Setup & Execution

### Prerequisites
- PHP >= 8.2
- Composer
- Node.js & npm
- SQLite / MySQL

### Quick Start
```bash
# 1. Install PHP dependencies
composer install

# 2. Environment Setup
cp .env.example .env
php artisan key:generate

# 3. Frontend Compilation
npm install
npm run build

# 4. Database Setup & Seeding
php artisan migrate --seed

# 5. Serve Application
php artisan serve --port=8081
```

Access the application in your browser at `http://localhost:8081`.

---

## 🔗 Serving API Integration
FPLIP Investigate connects to `fplip-core` FastAPI serving endpoints via standard HTTP client calls configured in `.env`:

```env
FASTAPI_BASE_URL=http://127.0.0.1:8000
FASTAPI_API_KEY=your_api_key_here
FASTAPI_TIMEOUT=90
```
