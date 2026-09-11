# 🔎 FPLIP Investigate — Operational Web Application

**FPLIP Investigate** is the operational web application module of the Factory Performance & Loss Intelligence Platform. Built with Laravel 11, Tailwind CSS, and Vite, it bridges plant floor operations with backend data platform intelligence.

---

## 📸 Application Screenshots & Workflow Features

### 1. Secure Authentication & Role-Based Access Control (RBAC)
Provides specialized user roles and permissions for **Plant Managers** and **Line Technicians**.

![Laravel Investigate Login](../assets/demo-screenshots/15_laravel_investigate_login.png)
*Figure 1: FPLIP Investigate Secure Portal Login*

---

### 2. Plant Signal Intelligence Dashboard
Monitors real-time OEE telemetry streams, shift filters, and active plant performance metrics.

![Plant Signal Intelligence Dashboard](../assets/demo-screenshots/16_plant_signal_intelligence_dashboard.png)
*Figure 2: Plant Signal Intelligence Dashboard with Live Telemetry Stream and Shift Inspector*

---

### 3. Active Anomaly Signal Cards & Investigation Triggers
Automated signal cards trigger work orders when OEE drops below 75% or scrap exceeds 5%.

![Active Plant Signals Cards](../assets/demo-screenshots/17_active_plant_signals_cards.png)
*Figure 3: Active Anomaly Signal Cards triggering automated technician dispatches*

---

### 4. Grounded Gemini AI Operational Diagnostic
Integrates with Gemini LLM APIs restricted to 4 deterministic tool functions to synthesize plain-language root-cause explanations without hallucination.

![Gemini AI Operational Diagnostic](../assets/demo-screenshots/18_gemini_ai_operational_diagnostic.png)
*Figure 4: Grounded Gemini AI Diagnostic drawer providing executive summaries and action items*

---

### 5. Line Technician Root Cause Work Order Form
Floor-level repair logging, physical finding description, corrective action entry, and immutable audit trail generation.

![Technician Work Order Form](../assets/demo-screenshots/19_technician_root_cause_submission_form.png)
*Figure 5: Line Technician Root Cause Submission Form and Fix Log*

---

## 🎯 Key Application Capabilities

- **Role-Based Workflows**: Tailored user dashboards for **Plant Managers** and **Technicians**.
- **Investigation Lifecycle**: Detect $\rightarrow$ Investigate $\rightarrow$ Assign $\rightarrow$ Fix $\rightarrow$ Close.
- **AI-Powered Explanations**: Grounded LLM diagnostic drawer providing clear action plans.
- **Audit Trail Governance**: Complete historical tracking of all user actions and anomaly state changes.

---

## 🌐 Live Production Deployment

**FPLIP Investigate** is deployed and active on **Vercel Serverless Infrastructure**:

- **Live Application URL**: **[https://fplip-investigate-f.vercel.app](https://fplip-investigate-f.vercel.app)**

### 🔑 Pre-Seeded Test Credentials
The login portal features convenient 1-click test buttons for instantaneous role switching:
- **Plant Manager**: `manager@fplip.test` / Password: `password`
- **Line Technician**: `technician1@fplip.test` / Password: `password`

### Serverless Architecture on Vercel (`api/index.php` + `vercel.json`)
- **Runtime**: `vercel-php@0.7.3` serverless function.
- **Dynamic File Storage**: Automatically prepares `/tmp/storage` and symlinks SQLite database for zero-downtime serverless execution.
- **Asset Bundling**: Automated Vite asset compilation to `public/build` served via CDN edge caching with forced HTTPS.

---

## 🐳 Docker Containerization (`Dockerfile`)

The application features a fully optimized multi-stage Docker build:

### Build & Run via Docker
```bash
cd fplip-investigate

# 1. Build the multi-stage Docker image
docker build -t fplip-investigate .

# 2. Run the container on port 8081
docker run -d -p 8081:8081 --name fplip-investigate-app fplip-investigate

# 3. View container logs
docker logs -f fplip-investigate-app
```

- **Access URL**: `http://localhost:8081`
- **Multi-Stage Structure**:
  - `Stage 1 (Node 20 Alpine)`: Compiles Tailwind CSS and Vite bundle to `/app/public/build`.
  - `Stage 2 (PHP 8.2 CLI)`: Lean production runtime with SQLite PDO, Zip, BCMath, and automated database seeder entrypoint (`docker-entrypoint.sh`).

---

## 🚀 Local Development Setup

### Prerequisites
- PHP $\ge$ 8.2
- Composer
- Node.js & npm
- SQLite / MySQL

### Quick Start
```bash
cd fplip-investigate

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
FASTAPI_BASE_URL=https://fplip-api.vercel.app
FASTAPI_API_KEY=your_api_key_here
FASTAPI_TIMEOUT=90
```

