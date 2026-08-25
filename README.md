# Dialysis Adequacy Kt/V Calculator

> **Nephrology** — Hemodialysis Adequacy Assessment

## Overview

Real clinical calculator for hemodialysis adequacy using the Daugirdas II formula for single-pool Kt/V, equilibrated Kt/V, URR, standard Kt/V, and normalized protein catabolic rate (nPCR).

**References:** KDOQI 2015, Daugirdas JT (Semin Dial 2001), Gotch FA

## Formulas Implemented

| Calculator | Formula |
|:-----------|:--------|
| **spKt/V** | -ln(R - 0.008×t) + (4 - 3.5×R) × UF/W |
| **URR** | (PreBUN - PostBUN) / PreBUN × 100 |
| **eKt/V** | spKt/V - 0.6 × (spKt/V/t) + 0.03 |
| **stdKt/V** | (10080 × spKt/V) / (weekly_time × (1-e^(-spKt/V/t)) + 10080 - weekly_time) |
| **nPCR** | G = (Vd_pre×PreBUN - Vd_post×PostBUN) / t; nPCR = G×1440 / (Vd×1000) |

## CLI Usage

```bash
# Single-pool Kt/V
python ktv_sentinel.py spktv --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75

# URR
python ktv_sentinel.py urr --pre-bun 60 --post-bun 15

# Equilibrated Kt/V
python ktv_sentinel.py ektv --spktv 1.4 --time 4

# Standard Kt/V
python ktv_sentinel.py stdktv --spktv 1.4 --sessions 3 --time 4

# nPCR
python ktv_sentinel.py npcr --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75

# Full assessment
python ktv_sentinel.py full --pre-bun 60 --post-bun 15 --time 4 --uf-l 2.5 --weight 75
```

## Python API

```python
from ktv_sentinel import calc_spktv, calc_urr, calc_ektv, full_adequacy_assessment

# spKt/V
result = calc_spktv(pre_bun=60, post_bun=15, dialysis_time_hr=4,
                    uf_volume_l=2.5, post_weight_kg=75)
print(result["spktv"])  # ~1.4
print(result["adequate"])  # True

# Full assessment
full = full_adequacy_assessment(60, 15, 4, 2.5, 75)
```

## Adequacy Targets

| Parameter | Target |
|:----------|:-------|
| spKt/V (HD 3x/week) | ≥ 1.2 |
| eKt/V | ≥ 1.2 |
| URR | ≥ 65% |
| stdKt/V | ≥ 2.0 |
| nPCR | 0.8-1.4 g/kg/day |

## License

MIT License.
