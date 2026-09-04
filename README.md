# Dialysis Adequacy Ktv Agent

> **Domain:** Nephrology & Renal Replacement Protocols  
> **Reference Guidelines & Standards:** `KDIGO & KDOQI Clinical Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Dialysis Adequacy Ktv Agent** is an advanced analytical and computational platform implementing Hemodialysis Daugirdas II Single-Pool spKt/V & nPCR Agent.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calc_spktv()`**: Single-pool Kt/V using Daugirdas II formula.

spKt/V = -ln(R - 0.008 × t) + (4 - 3.5 × R) × UF/W

where:
    R = Post-dialysis BUN / Pre-dialysis BUN
    t = dialysis time in hours
    UF = ultrafiltration volume in liters
    W = post-dialysis weight in kg

Args:
    pre_bun: Pre-dialysis BUN (mg/dL)
    post_bun: Post-dialysis BUN (mg/dL)
    dialysis_time_hr: Dialysis session time in hours
    uf_volume_l: Ultrafiltration volume in liters
    post_weight_kg: Post-dialysis weight in kg

Returns:
    Dict with spKt/V and components
- **`calc_urr()`**: Urea Reduction Ratio (URR).

URR = (PreBUN - PostBUN) / PreBUN × 100

Target URR ≥ 65%

Args:
    pre_bun: Pre-dialysis BUN (mg/dL)
    post_bun: Post-dialysis BUN (mg/dL)

Returns:
    Dict with URR percentage and adequacy
- **`calc_ektv()`**: Equilibrated Kt/V (eKt/V) from spKt/V.

eKt/V = spKt/V - 0.6 × (spKt/V / t) + 0.03

Accounts for urea rebound after dialysis stops.

Args:
    spktv: Single-pool Kt/V
    dialysis_time_hr: Dialysis time in hours

Returns:
    Dict with eKt/V
- **`calc_stdktv()`**: Standard Kt/V (stdKt/V) for comparing different dialysis schedules.

stdKt/V ≈ (10080 × spKt/V) / (t × sessions_per_week × (1 - e^(-spKt/V/t)) + 10080 - t × sessions_per_week)

Simplified: stdKt/V = spKt/V × 7 / (sessions_per_week × (1 + 0.47 × spKt/V / t))

Target: stdKt/V ≥ 2.0 (HD), ≥ 1.7 (PD weekly)

Args:
    spktv: Single-pool Kt/V per session
    sessions_per_week: Number of sessions per week
    dialysis_time_hr: Hours per session

Returns:
    Dict with stdKt/V
- **`calc_nPCR()`**: Normalized Protein Catabolic Rate (nPCR) from pre/post BUN.

nPCR (g/kg/day) = (C0 - Ct + UF × Ct/Vd) / (t/24) / Vd_normalized + 0.17

Simplified Borah formula:
nPCR = 0.01 × (pre_BUN - post_BUN) / (t/24) + 0.17
adjusted for volume of distribution.

More accurate (Gotch):
G (mg/min) = (V2 × C2 - V1 × C1) / t
where V1 = post-weight × 0.6, V2 = V1 + UF
nPCR = G / (V1 / 0.6) / 1000 × 1440

Args:
    pre_bun: Pre-dialysis BUN (mg/dL)
    post_bun: Post-dialysis BUN (mg/dL)
    dialysis_time_hr: Session duration (hours)
    uf_volume_l: Ultrafiltration volume (liters)
    post_weight_kg: Post-dialysis weight (kg)
    interdialytic_interval_hr: Hours between sessions (default 48)
    interdialytic_weight_gain_kg: Weight gain between sessions (kg)

Returns:
    Dict with nPCR

---

## 📐 Mathematical Formulation & Logic

```text
  - Single-pool Kt/V (spKt/V) via Daugirdas II formula
  Single-pool Kt/V using Daugirdas II formula.
  Daugirdas II formula
  Standard Kt/V formula (Gotch)
  Simplified Borah formula:
```

---

## 💻 CLI Quickstart & Usage

### 1. Kt/V Sentinel CLI (root `cli.py`)
```bash
# Single-pool Kt/V
python cli.py spktv --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75

# Urea Reduction Ratio
python cli.py urr --pre-bun 60 --post-bun 15

# Equilibrated Kt/V
python cli.py ektv --spktv 1.4 --time 4

# Standard Kt/V
python cli.py stdktv --spktv 1.4 --sessions 3 --time 4

# Normalized Protein Catabolic Rate
python cli.py npcr --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75

# Full adequacy assessment
python cli.py full --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75 --sessions 3
```

### 2. Dialysis Coordinators CLI (`dialysis_adequacy_ktv_agent/cli.py`)
```bash
# Clinical audit
python dialysis_adequacy_ktv_agent_app.py audit --case-id CASE-001 --primary 26.2 --status DISCORDANT

# Batch processing from CSV
python dialysis_adequacy_ktv_agent_app.py batch -i sample.csv -o results.csv

# System chat
python dialysis_adequacy_ktv_agent_app.py chat "status summary"

# Launch FastAPI server
python dialysis_adequacy_ktv_agent_app.py serve --host 127.0.0.1 --port 8000
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient names.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable in production to ensure audit trail integrity across restarts:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

Without this variable, an ephemeral key is generated at runtime (with a warning), making cross-restart verification impossible.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t dialysis-adequacy-ktv-agent .
docker run -p 8000:8000 dialysis-adequacy-ktv-agent
```
