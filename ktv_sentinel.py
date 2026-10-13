#!/usr/bin/env python3
"""Dialysis urea-kinetic estimates for educational and audit use.

Clinical interpretation depends on dialysis schedule, specimen collection,
residual kidney function and an independent clinical review.
"""
import argparse
import json
import math
import sys
from typing import Any, Dict


def _finite_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")


def _session_inputs(pre_bun: float, post_bun: float,
                    dialysis_time_hr: float, uf_volume_l: float,
                    post_weight_kg: float) -> None:
    for name, val in (("Pre-dialysis BUN", pre_bun),
                      ("Post-dialysis BUN", post_bun),
                      ("Dialysis time", dialysis_time_hr),
                      ("Post-dialysis weight", post_weight_kg)):
        _finite_positive(name, val)
    if post_bun >= pre_bun:
        raise ValueError("Post-dialysis BUN must be less than pre-dialysis BUN")
    if not math.isfinite(uf_volume_l) or uf_volume_l < 0:
        raise ValueError("Ultrafiltration volume must be finite and nonnegative")
    if dialysis_time_hr > 24:
        raise ValueError("Dialysis time must not exceed 24 hours")


def calc_spktv(pre_bun: float, post_bun: float, dialysis_time_hr: float,
               uf_volume_l: float, post_weight_kg: float) -> Dict[str, Any]:
    """Second-generation Daugirdas spKt/V; t hours, UF liters, W kg."""
    _session_inputs(pre_bun, post_bun, dialysis_time_hr, uf_volume_l, post_weight_kg)
    ratio = post_bun / pre_bun
    log_arg = ratio - 0.008 * dialysis_time_hr
    if log_arg <= 0:
        raise ValueError("R - 0.008*t must be positive (logarithm domain)")
    spktv = -math.log(log_arg) + (4 - 3.5 * ratio) * (uf_volume_l / post_weight_kg)
    if not math.isfinite(spktv) or spktv <= 0:
        raise ValueError("Computed spKt/V is outside the valid domain")
    return {
        "spktv": round(spktv, 3), "R_ratio": round(ratio, 4),
        "pre_bun": pre_bun, "post_bun": post_bun,
        "dialysis_time_hr": dialysis_time_hr, "uf_volume_l": uf_volume_l,
        "post_weight_kg": post_weight_kg,
        "minimum_spktv": 1.2, "target_spktv": 1.4,
        "adequate": spktv >= 1.2,
        "recommendation": ("Meets the KDOQI minimum of 1.2 for thrice-weekly HD; "
                           "the prescribed target is 1.4."
                           if spktv >= 1.2 else
                           "Below the KDOQI minimum of 1.2 for thrice-weekly HD; "
                           "verify sampling and review clinically."),
    }


def calc_urr(pre_bun: float, post_bun: float) -> Dict[str, Any]:
    """Urea reduction ratio; a screening proxy, not a substitute for Kt/V."""
    _finite_positive("Pre-dialysis BUN", pre_bun)
    if not math.isfinite(post_bun) or post_bun < 0 or post_bun >= pre_bun:
        raise ValueError("Post-dialysis BUN must be finite, nonnegative, and less than pre-BUN")
    urr = 100.0 * (pre_bun - post_bun) / pre_bun
    return {"urr_percent": round(urr, 1), "pre_bun": pre_bun,
            "post_bun": post_bun, "target_urr_percent": 65.0,
            "adequate": urr >= 65,
            "recommendation": "URR is a screening measure; evaluate spKt/V and clinical context."}


def calc_ektv(spktv: float, dialysis_time_hr: float) -> Dict[str, Any]:
    """Rate-equation arterial-access estimate of eKt/V (not direct measurement).

    Daugirdas/Schneditz: eKt/V = spKt/V - 0.60*spKt/V/t + 0.03.
    """
    _finite_positive("spKt/V", spktv)
    _finite_positive("Dialysis time", dialysis_time_hr)
    if dialysis_time_hr < 2 or dialysis_time_hr > 24:
        raise ValueError("The eKt/V rate equation requires 2 to 24 hours")
    ektv = spktv - 0.6 * spktv / dialysis_time_hr + 0.03
    if not math.isfinite(ektv) or ektv <= 0:
        raise ValueError("Computed eKt/V is outside the valid domain")
    return {"ektv": round(ektv, 3), "spktv": spktv,
            "dialysis_time_hr": dialysis_time_hr,
            "target_ektv": None, "adequate": None,
            "recommendation": "Estimated eKt/V; no independent universal eKt/V threshold applied."}


def calc_stdktv(spktv: float, sessions_per_week: float = 3.0,
                dialysis_time_hr: float = 4.0) -> Dict[str, Any]:
    """Approximate weekly standard Kt/V from a fixed-volume Leypoldt model.

    stdKt/V = [168*(1-exp(-eKt/V))/t] /
              [(1-exp(-eKt/V))/eKt/V + 168/(N*t) - 1]
    t in hours; excludes residual renal urea clearance.
    """
    _finite_positive("spKt/V", spktv)
    _finite_positive("Dialysis time", dialysis_time_hr)
    _finite_positive("Sessions per week", sessions_per_week)
    if dialysis_time_hr < 2 or dialysis_time_hr > 24:
        raise ValueError("Treatment duration must be between 2 and 24 hours")
    if sessions_per_week != int(sessions_per_week) or not 1 <= sessions_per_week <= 7:
        raise ValueError("Sessions per week must be an integer from 1 to 7")
    ektv = calc_ektv(spktv, dialysis_time_hr)["ektv"]
    # Calculate from unrounded eKt/V to avoid premature rounding.
    ek = spktv - 0.6 * spktv / dialysis_time_hr + 0.03
    fraction = -math.expm1(-ek)
    denom = fraction / ek + 168 / (sessions_per_week * dialysis_time_hr) - 1
    if denom <= 0:
        raise ValueError("Invalid standardized Kt/V denominator")
    result = 168 * fraction / dialysis_time_hr / denom
    return {
        "stdktv": round(result, 3), "spktv_per_session": spktv,
        "ektv_estimate": ektv, "sessions_per_week": int(sessions_per_week),
        "dialysis_time_hr": dialysis_time_hr,
        "minimum_stdktv": 2.1, "target_stdktv": 2.3,
        "adequate": result >= 2.1,
        "recommendation": ("For non-thrice-weekly HD, KDOQI suggests a weekly "
                           "target of 2.3 and minimum of 2.1; this fixed-volume "
                           "estimate excludes residual renal function."),
    }


def calc_nPCR(pre_bun: float, post_bun: float, dialysis_time_hr: float,
              uf_volume_l: float, post_weight_kg: float,
              interdialytic_interval_hr: float = 48.0,
              interdialytic_weight_gain_kg: float = 2.0,
              session_position: str = "midweek") -> Dict[str, Any]:
    """Estimate nPCR for thrice-weekly HD using Depner-Daugirdas equations.

    Default assumes a midweek sample and negligible residual renal function.
    The two legacy interdialytic parameters are accepted for compatibility,
    but are not inputs to these published two-point equations.
    """
    _session_inputs(pre_bun, post_bun, dialysis_time_hr, uf_volume_l, post_weight_kg)
    _finite_positive("Interdialytic interval", interdialytic_interval_hr)
    if not math.isfinite(interdialytic_weight_gain_kg) or interdialytic_weight_gain_kg < 0:
        raise ValueError("Interdialytic weight gain must be finite and nonnegative")
    # Coefficients by position in a thrice-weekly HD schedule.
    coefficients = {"beginning": (36.3, 5.48, 53.5),
                    "midweek": (25.8, 1.15, 56.4),
                    "end": (16.3, 4.30, 56.6)}
    if session_position not in coefficients:
        raise ValueError("session_position must be beginning, midweek or end")
    ktv = -math.log(post_bun / pre_bun - 0.008 * dialysis_time_hr) + (
        4 - 3.5 * post_bun / pre_bun) * (uf_volume_l / post_weight_kg) if (
        post_bun / pre_bun - 0.008 * dialysis_time_hr) > 0 else None
    if ktv is None or ktv <= 0 or not math.isfinite(ktv):
        raise ValueError("Invalid spKt/V for nPCR estimate")
    a, b, c = coefficients[session_position]
    npcr = pre_bun / (a + b * ktv + c / ktv) + 0.168
    status = "low" if npcr < 0.8 else "high" if npcr > 1.4 else "adequate"
    return {
        "npcr_g_kg_day": round(npcr, 3),
        "npcr_simplified": round(npcr, 3),
        "generation_rate_mg_min": None, "vd_post_l": None, "vd_pre_l": None,
        "pre_bun": pre_bun, "post_bun": post_bun,
        "status": status, "target_range": "context dependent",
        "session_position": session_position,
        "method": "Depner-Daugirdas two-point equation (thrice-weekly HD)",
        "recommendation": ("Estimate assumes a thrice-weekly schedule and minimal "
                           "residual urea clearance; cannot diagnose nutrition on its own."),
    }


def full_adequacy_assessment(pre_bun: float, post_bun: float,
                              dialysis_time_hr: float, uf_volume_l: float,
                              post_weight_kg: float,
                              sessions_per_week: float = 3.0,
                              session_position: str = "midweek") -> Dict[str, Any]:
    """Return component estimates. nPCR is omitted outside thrice-weekly HD."""
    sp = calc_spktv(pre_bun, post_bun, dialysis_time_hr, uf_volume_l, post_weight_kg)
    urr = calc_urr(pre_bun, post_bun)
    ek = calc_ektv(sp["spktv"], dialysis_time_hr)
    std = calc_stdktv(sp["spktv"], sessions_per_week, dialysis_time_hr)
    npcr = (calc_nPCR(pre_bun, post_bun, dialysis_time_hr, uf_volume_l,
                     post_weight_kg, session_position=session_position)
            if sessions_per_week == 3 else None)
    return {
        "spktv": sp, "urr": urr, "ektv": ek, "stdktv": std,
        "npcr": npcr,
        "overall_adequate": (sp["adequate"] and urr["adequate"]
                             if sessions_per_week == 3 else std["adequate"]),
        "interpretation": ("Screening thresholds only; not a prescription decision. "
                           "Verify urea sampling and residual renal function."),
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
    p_npcr.add_argument("--position", choices=["beginning", "midweek", "end"], default="midweek")

    # Full assessment
    p_full = sub.add_parser("full", help="Full adequacy assessment")
    p_full.add_argument("--pre-bun", type=float, required=True, help="Pre-dialysis BUN")
    p_full.add_argument("--post-bun", type=float, required=True, help="Post-dialysis BUN")
    p_full.add_argument("--time", type=float, required=True, help="Dialysis time (hours)")
    p_full.add_argument("--uf-l", type=float, required=True, help="UF volume (liters)")
    p_full.add_argument("--weight", type=float, required=True, help="Post-dialysis weight (kg)")
    p_full.add_argument("--sessions", type=float, default=3.0, help="Sessions per week")
    p_full.add_argument("--position", choices=["beginning", "midweek", "end"], default="midweek")

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
        result = calc_nPCR(args.pre_bun, args.post_bun, args.time, args.uf_l, args.weight,
                           session_position=args.position)
    elif args.command == "full":
        result = full_adequacy_assessment(args.pre_bun, args.post_bun, args.time,
                                           args.uf_l, args.weight, args.sessions, args.position)
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
