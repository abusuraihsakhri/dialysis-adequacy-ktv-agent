#!/usr/bin/env python3
"""
Dialysis Adequacy Kt/V Calculator

Real implementations for:
- Single-pool Kt/V (spKt/V) via Daugirdas II formula
- Equilibrated Kt/V (eKt/V)
- URR (Urea Reduction Ratio)
- Standard Kt/V (stdKt/V) for peritoneal dialysis
- Normalized Protein Catabolic Rate (nPCR)

References: KDOQI 2015, Daugirdas JT (Semin Dial 2001)
Stdlib only.
"""

import argparse
import json
import math
import sys
from typing import Dict, Any


def calc_spktv(pre_bun: float, post_bun: float, dialysis_time_hr: float,
               uf_volume_l: float, post_weight_kg: float) -> Dict[str, Any]:
    """
    Single-pool Kt/V using Daugirdas II formula.

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
    """
    if pre_bun <= 0:
        raise ValueError("Pre-dialysis BUN must be positive")
    if post_bun <= 0:
        raise ValueError("Post-dialysis BUN must be positive")
    if post_bun >= pre_bun:
        raise ValueError("Post-dialysis BUN must be less than pre-dialysis BUN")
    if dialysis_time_hr <= 0:
        raise ValueError("Dialysis time must be positive")
    if post_weight_kg <= 0:
        raise ValueError("Post-dialysis weight must be positive")

    R = post_bun / pre_bun
    t = dialysis_time_hr
    UF = uf_volume_l
    W = post_weight_kg

    # Daugirdas II formula
    spktv = -math.log(R - 0.008 * t) + (4 - 3.5 * R) * (UF / W)

    adequate = spktv >= 1.2

    return {
        "spktv": round(spktv, 3),
        "R_ratio": round(R, 4),
        "pre_bun": pre_bun,
        "post_bun": post_bun,
        "dialysis_time_hr": dialysis_time_hr,
        "uf_volume_l": uf_volume_l,
        "post_weight_kg": post_weight_kg,
        "target_spktv": 1.2,
        "adequate": adequate,
        "recommendation": ("Adequate dialysis (spKt/V ≥ 1.2)." if adequate
                           else "Inadequate dialysis. Consider increasing time, blood flow, or dialyzer size."),
    }


def calc_urr(pre_bun: float, post_bun: float) -> Dict[str, Any]:
    """
    Urea Reduction Ratio (URR).

    URR = (PreBUN - PostBUN) / PreBUN × 100

    Target URR ≥ 65%

    Args:
        pre_bun: Pre-dialysis BUN (mg/dL)
        post_bun: Post-dialysis BUN (mg/dL)

    Returns:
        Dict with URR percentage and adequacy
    """
    if pre_bun <= 0:
        raise ValueError("Pre-dialysis BUN must be positive")
    if post_bun < 0:
        raise ValueError("Post-dialysis BUN cannot be negative")
    if post_bun >= pre_bun:
        raise ValueError("Post-dialysis BUN must be less than pre-dialysis BUN")

    urr = ((pre_bun - post_bun) / pre_bun) * 100.0
    adequate = urr >= 65.0

    return {
        "urr_percent": round(urr, 1),
        "pre_bun": pre_bun,
        "post_bun": post_bun,
        "target_urr_percent": 65.0,
        "adequate": adequate,
        "recommendation": ("URR ≥ 65%: Adequate dialysis." if adequate
                           else "URR < 65%: Inadequate dialysis. Review treatment parameters."),
    }


def calc_ektv(spktv: float, dialysis_time_hr: float) -> Dict[str, Any]:
    """
    Equilibrated Kt/V (eKt/V) from spKt/V.

    eKt/V = spKt/V - 0.6 × (spKt/V / t) + 0.03

    Accounts for urea rebound after dialysis stops.

    Args:
        spktv: Single-pool Kt/V
        dialysis_time_hr: Dialysis time in hours

    Returns:
        Dict with eKt/V
    """
    if dialysis_time_hr <= 0:
        raise ValueError("Dialysis time must be positive")

    ektv = spktv - 0.6 * (spktv / dialysis_time_hr) + 0.03

    return {
        "ektv": round(ektv, 3),
        "spktv": spktv,
        "dialysis_time_hr": dialysis_time_hr,
        "target_ektv": 1.2,
        "adequate": ektv >= 1.2,
        "recommendation": ("eKt/V adequate (≥ 1.2)." if ektv >= 1.2
                           else "eKt/V below target. Consider extending session."),
    }


def calc_stdktv(spktv: float, sessions_per_week: float = 3.0,
                dialysis_time_hr: float = 4.0) -> Dict[str, Any]:
    """
    Standard Kt/V (stdKt/V) for comparing different dialysis schedules.

    stdKt/V ≈ (10080 × spKt/V) / (t × sessions_per_week × (1 - e^(-spKt/V/t)) + 10080 - t × sessions_per_week)

    Simplified: stdKt/V = spKt/V × 7 / (sessions_per_week × (1 + 0.47 × spKt/V / t))

    Target: stdKt/V ≥ 2.0 (HD), ≥ 1.7 (PD weekly)

    Args:
        spktv: Single-pool Kt/V per session
        sessions_per_week: Number of sessions per week
        dialysis_time_hr: Hours per session

    Returns:
        Dict with stdKt/V
    """
    if spktv <= 0:
        raise ValueError("spKt/V must be positive")
    if sessions_per_week <= 0:
        raise ValueError("Sessions per week must be positive")
    if dialysis_time_hr <= 0:
        raise ValueError("Dialysis time must be positive")

    # Standard Kt/V formula (Gotch)
    weekly_time = sessions_per_week * dialysis_time_hr
    equilibration_factor = 1 - math.exp(-spktv / dialysis_time_hr)
    if equilibration_factor == 0:
        equilibration_factor = 0.001

    stdktv = (10080 * spktv) / (weekly_time * equilibration_factor + 10080 - weekly_time)

    target = 2.0
    adequate = stdktv >= target

    return {
        "stdktv": round(stdktv, 3),
        "spktv_per_session": spktv,
        "sessions_per_week": sessions_per_week,
        "dialysis_time_hr": dialysis_time_hr,
        "target_stdktv": target,
        "adequate": adequate,
        "recommendation": ("stdKt/V adequate (≥ 2.0)." if adequate
                           else "stdKt/V below target. Increase frequency or session dose."),
    }


def calc_nPCR(pre_bun: float, post_bun: float, dialysis_time_hr: float,
              uf_volume_l: float, post_weight_kg: float,
              interdialytic_interval_hr: float = 48.0,
              interdialytic_weight_gain_kg: float = 2.0) -> Dict[str, Any]:
    """
    Normalized Protein Catabolic Rate (nPCR) from pre/post BUN.

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
    """
    if pre_bun <= 0 or post_bun < 0:
        raise ValueError("BUN values must be positive")
    if post_weight_kg <= 0:
        raise ValueError("Weight must be positive")

    # Volume of distribution (L) - Watson approximation
    vd_post = 0.6 * post_weight_kg  # post-dialysis
    vd_pre = vd_post + uf_volume_l   # pre-dialysis

    # Generation rate calculation
    # G (mg/min) = (Vd_pre × pre_BUN - Vd_post × post_BUN) / (t × 60)
    # Convert BUN from mg/dL to mg/L: × 10
    t_min = dialysis_time_hr * 60.0
    generation_mg_min = (vd_pre * pre_bun * 10 - vd_post * post_bun * 10) / t_min

    # nPCR = G / Vd_post (normalized) × 1440 min/day / 1000 (mg to g)
    # nPCR (g/kg/day) = G × 1440 / (Vd_post × 1000) / weight
    npcr = (generation_mg_min * 1440.0) / (vd_post * 1000.0)

    # Simplified alternative (Borah)
    npcr_simplified = 0.01 * (pre_bun - post_bun) / (dialysis_time_hr / 24.0) + 0.17

    # Interpretation
    if npcr < 0.8:
        status = "low"
        recommendation = "nPCR < 0.8 g/kg/day: Possible protein intake insufficiency. Nutritional counseling."
    elif npcr <= 1.4:
        status = "adequate"
        recommendation = "nPCR 0.8-1.4 g/kg/day: Adequate protein intake."
    else:
        status = "high"
        recommendation = "nPCR > 1.4 g/kg/day: High protein catabolism. Evaluate for infection/hypercatabolism."

    return {
        "npcr_g_kg_day": round(npcr, 3),
        "npcr_simplified": round(npcr_simplified, 3),
        "generation_rate_mg_min": round(generation_mg_min, 2),
        "vd_post_l": round(vd_post, 1),
        "vd_pre_l": round(vd_pre, 1),
        "pre_bun": pre_bun,
        "post_bun": post_bun,
        "status": status,
        "target_range": "0.8-1.4 g/kg/day",
        "recommendation": recommendation,
    }


def full_adequacy_assessment(pre_bun: float, post_bun: float,
                              dialysis_time_hr: float, uf_volume_l: float,
                              post_weight_kg: float,
                              sessions_per_week: float = 3.0) -> Dict[str, Any]:
    """
    Complete dialysis adequacy assessment.

    Returns spKt/V, eKt/V, stdKt/V, URR, and nPCR.
    """
    sp = calc_spktv(pre_bun, post_bun, dialysis_time_hr, uf_volume_l, post_weight_kg)
    urr = calc_urr(pre_bun, post_bun)
    ek = calc_ektv(sp["spktv"], dialysis_time_hr)
    std = calc_stdktv(sp["spktv"], sessions_per_week, dialysis_time_hr)
    npcr = calc_nPCR(pre_bun, post_bun, dialysis_time_hr, uf_volume_l, post_weight_kg)

    return {
        "spktv": sp,
        "urr": urr,
        "ektv": ek,
        "stdktv": std,
        "npcr": npcr,
        "overall_adequate": sp["adequate"] and urr["adequate"],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ktv-sentinel",
        description="Dialysis Adequacy Kt/V Calculator"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # spKt/V
    p_sp = sub.add_parser("spktv", help="Single-pool Kt/V (Daugirdas II)")
    p_sp.add_argument("--pre-bun", type=float, required=True, help="Pre-dialysis BUN (mg/dL)")
    p_sp.add_argument("--post-bun", type=float, required=True, help="Post-dialysis BUN (mg/dL)")
    p_sp.add_argument("--time", type=float, required=True, help="Dialysis time (hours)")
    p_sp.add_argument("--uf-l", type=float, required=True, help="UF volume (liters)")
    p_sp.add_argument("--weight", type=float, required=True, help="Post-dialysis weight (kg)")

    # URR
    p_urr = sub.add_parser("urr", help="Urea Reduction Ratio")
    p_urr.add_argument("--pre-bun", type=float, required=True, help="Pre-dialysis BUN")
    p_urr.add_argument("--post-bun", type=float, required=True, help="Post-dialysis BUN")

    # eKt/V
    p_ek = sub.add_parser("ektv", help="Equilibrated Kt/V")
    p_ek.add_argument("--spktv", type=float, required=True, help="spKt/V value")
    p_ek.add_argument("--time", type=float, required=True, help="Dialysis time (hours)")

    # stdKt/V
    p_std = sub.add_parser("stdktv", help="Standard Kt/V")
    p_std.add_argument("--spktv", type=float, required=True, help="spKt/V per session")
    p_std.add_argument("--sessions", type=float, default=3.0, help="Sessions per week")
    p_std.add_argument("--time", type=float, default=4.0, help="Hours per session")

    # nPCR
    p_npcr = sub.add_parser("npcr", help="Normalized Protein Catabolic Rate")
    p_npcr.add_argument("--pre-bun", type=float, required=True, help="Pre-dialysis BUN")
    p_npcr.add_argument("--post-bun", type=float, required=True, help="Post-dialysis BUN")
    p_npcr.add_argument("--time", type=float, required=True, help="Dialysis time (hours)")
    p_npcr.add_argument("--uf-l", type=float, required=True, help="UF volume (liters)")
    p_npcr.add_argument("--weight", type=float, required=True, help="Post-dialysis weight (kg)")

    # Full assessment
    p_full = sub.add_parser("full", help="Full adequacy assessment")
    p_full.add_argument("--pre-bun", type=float, required=True, help="Pre-dialysis BUN")
    p_full.add_argument("--post-bun", type=float, required=True, help="Post-dialysis BUN")
    p_full.add_argument("--time", type=float, required=True, help="Dialysis time (hours)")
    p_full.add_argument("--uf-l", type=float, required=True, help="UF volume (liters)")
    p_full.add_argument("--weight", type=float, required=True, help="Post-dialysis weight (kg)")
    p_full.add_argument("--sessions", type=float, default=3.0, help="Sessions per week")

    args = parser.parse_args(argv)

    if args.command == "spktv":
        result = calc_spktv(args.pre_bun, args.post_bun, args.time, args.uf_l, args.weight)
    elif args.command == "urr":
        result = calc_urr(args.pre_bun, args.post_bun)
    elif args.command == "ektv":
        result = calc_ektv(args.spktv, args.time)
    elif args.command == "stdktv":
        result = calc_stdktv(args.spktv, args.sessions, args.time)
    elif args.command == "npcr":
        result = calc_nPCR(args.pre_bun, args.post_bun, args.time, args.uf_l, args.weight)
    elif args.command == "full":
        result = full_adequacy_assessment(args.pre_bun, args.post_bun, args.time,
                                           args.uf_l, args.weight, args.sessions)
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
