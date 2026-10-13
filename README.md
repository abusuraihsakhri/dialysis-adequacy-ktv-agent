# Dialysis Adequacy — Kt/V Calculator

Hemodialysis urea-kinetic estimates for education, research and local audit.
The source contains a standalone browser calculator, a Python calculation CLI,
and a separate, legacy rule-based coordinator. **Not a clinical decision-support
system or a substitute for dialysis-unit measurement protocols.**

## Browser calculator

Open `web/index.html` in a current desktop or mobile browser, or serve the
repository root with `python -m http.server 8000` and visit
`http://localhost:8000/web/`. Enter paired BUN measurements, treatment
duration, ultrafiltration volume, post-dialysis weight, weekly frequency and
the sampling position in the dialysis week. Select **Calculate**; export
results as JSON if needed. The interface requires no accounts or packages.

**Privacy:** All browser calculations execute locally with JavaScript. No
measurements are transmitted by the application and no analytics or remote
scripts are included. Do not enter personally identifiable or patient data;
hosting providers may retain ordinary HTTP access logs.

## Calculations

| Result | Method and scope |
| --- | --- |
| spKt/V | Daugirdas second-generation logarithmic equation, based on pre/post BUN, treatment time, UF and post-treatment weight. |
| URR | `100 × (pre-BUN − post-BUN) / pre-BUN`. |
| eKt/V | Arterial-access rate-equation **estimate** from spKt/V and treatment duration (2 hours or longer). |
| Weekly stdKt/V | Leypoldt fixed-volume approximation from estimated eKt/V, duration and sessions/week. Excludes residual kidney clearance. |
| nPCR | Depner–Daugirdas two-point estimate for **thrice-weekly HD**, selected beginning/mid/end-of-week equations; otherwise not returned. Assumes negligible residual renal clearance. |

KDOQI 2015 recommends **spKt/V target 1.4, minimum delivered 1.2**
for conventional thrice-weekly hemodialysis. For other frequencies,
**weekly stdKt/V target 2.3, minimum 2.1** is suggested. URR ≥65% is a
supplementary screening reference; it does not replace spKt/V.

Inputs must be finite; post-BUN must be lower than pre-BUN, the Daugirdas
logarithm argument positive, UF nonnegative, duration 2–24 hours for the
full assessment and frequency an integer from 1–7/week. Equations and
thresholds require clinical interpretation and proper specimen sampling.

## Python usage

Requires Python 3.9+. For local development:

```bash
python -m pip install -e ".[server,test]"
python cli.py full --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75 --sessions 3
python cli.py spktv --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75
python cli.py urr --pre-bun 60 --post-bun 15
python -m pytest -q
node web/test_calculator.cjs
```

The command-line entry point `ktv-sentinel` exposes `spktv`, `urr`,
`ektv`, `stdktv`, `npcr` and `full` subcommands. The
`dialysis-adequacy-ktv-engine` command provides the older
`audit`, `batch`, `chat` and `serve` workflows.

The legacy audit's arbitrary metric thresholds are **demonstration rules
only**, not KDOQI or KDIGO clinical cutoffs. The mock chat provider does
not invoke an LLM or independently verify clinical information. The
heuristic identifier checker is not an assurance of HIPAA de-identification.

### Optional HTTP service

```bash
dialysis-adequacy-ktv-engine serve --host 127.0.0.1 --port 8000
```

The `POST /api/adequacy` endpoint accepts JSON keys:
`pre_bun`, `post_bun`, `dialysis_time_hr`, `uf_volume_l`,
`post_weight_kg` and optional `sessions_per_week`.
`GET /health` provides a health check. The legacy demonstration
endpoints remain available at `/api/audit` and `/api/chat`.
**The HTTP service has no user authentication: do not expose it publicly
or submit patient information.**

For Docker, set a strong private `AUDIT_SECRET_KEY` environment
variable before `docker compose up --build`. Compose binds to
`127.0.0.1:8000` by default. Logs are held in process memory and the
audit trail is not a durable record system.

## Technology and tests

Python standard-library numeric calculations; FastAPI/Pydantic for the
optional service; HTML, CSS and dependency-free JavaScript in the browser.
Compatible with modern Chromium, Firefox and Safari (support for
`Math.expm1` required). GitHub Actions runs Python and Node regression
tests on Python 3.10–3.12. The browser UI uses JavaScript rather than
Pyodide because its equations do not require a Python runtime.

## Clinical sources

- [KDOQI Clinical Practice Guideline for Hemodialysis Adequacy, 2015 Update](https://www.sciencedirect.com/science/article/pii/S0272638615010197)
- [Leypoldt et al., calculation of weekly standard Kt/V, 2003](https://doi.org/10.1046/j.1492-7535.2003.01216.x)
- [Depner and Daugirdas, two-point normalized protein catabolic rate equations, 1996](https://pubmed.ncbi.nlm.nih.gov/8738814/)
- [Daugirdas and colleagues, simplified eKt/V rate equation](https://pubmed.ncbi.nlm.nih.gov/8591121/)

## License

MIT — see [LICENSE](LICENSE).
