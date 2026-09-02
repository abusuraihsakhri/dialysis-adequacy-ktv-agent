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

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

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
