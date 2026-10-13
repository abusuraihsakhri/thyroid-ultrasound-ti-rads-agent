"""Deterministic adult ACR TI-RADS (2017) nodule scoring.

Inputs are clinician-identified ultrasound descriptors, not image predictions.
Reference: Tessler et al., J Am Coll Radiol. 2017;14:587-595.
DOI: 10.1016/j.jacr.2017.01.046
"""
from __future__ import annotations

import math

COMPOSITION = {
    "cystic": 0,
    "spongiform": 0,
    "mixed": 1,
    "solid": 2,
}
ECHOGENICITY = {
    "isoechoic_hyperechoic": 1,
    "hypoechoic": 2,
    "very_hypoechoic": 3,
}
SHAPE = {"wider_than_tall": 0, "taller_than_wide": 3}
MARGIN = {
    "smooth": 0,
    "ill_defined": 0,
    "lobulated_irregular": 2,
    "extrathyroidal_extension": 3,
}
FOCI = {
    "macrocalcifications": 1,
    "rim_calcifications": 2,
    "punctate_foci": 3,
}
FOLLOWUP_YEARS = {
    "TR3": [1, 3, 5],
    "TR4": [1, 2, 3, 5],
    "TR5": [1, 2, 3, 4, 5],
}
THRESHOLDS_CM = {
    "TR3": (1.5, 2.5),
    "TR4": (1.0, 1.5),
    "TR5": (0.5, 1.0),
}


def score_tirads(
    *,
    composition: str,
    size_cm: float,
    echogenicity: str | None = None,
    shape: str | None = None,
    margin: str | None = None,
    echogenic_foci: list[str] | None = None,
) -> dict:
    """Compute ACR TI-RADS points and management thresholds.

    Completely/almost completely cystic or spongiform nodules are TR1
    regardless of additional non-scored features. Size means maximum diameter.
    """
    if composition not in COMPOSITION:
        raise ValueError("Invalid composition")
    if isinstance(size_cm, bool) or not isinstance(size_cm, (int, float)):
        raise ValueError("size_cm must be a positive finite number")
    if not math.isfinite(size_cm) or size_cm <= 0:
        raise ValueError("size_cm must be a positive finite number")
    if not isinstance(echogenic_foci, list):
        raise ValueError("echogenic_foci must be a list")
    if any(focus not in FOCI for focus in echogenic_foci):
        raise ValueError("Invalid echogenic focus")
    if len(echogenic_foci) != len(set(echogenic_foci)):
        raise ValueError("Duplicate echogenic focus")

    if composition in ("cystic", "spongiform"):
        if any((echogenicity is not None, shape is not None,
                margin is not None, bool(echogenic_foci))):
            raise ValueError("Do not score other features of cystic or spongiform nodules")
        components = {
            "composition": 0, "echogenicity": 0,
            "shape": 0, "margin": 0, "echogenic_foci": 0,
        }
    else:
        if echogenicity not in ECHOGENICITY:
            raise ValueError("Invalid or missing echogenicity")
        if shape not in SHAPE:
            raise ValueError("Invalid or missing shape")
        if margin not in MARGIN:
            raise ValueError("Invalid or missing margin")
        components = {
            "composition": COMPOSITION[composition],
            "echogenicity": ECHOGENICITY[echogenicity],
            "shape": SHAPE[shape],
            "margin": MARGIN[margin],
            "echogenic_foci": sum(FOCI[f] for f in echogenic_foci),
        }

    points = sum(components.values())
    if points == 0:
        category, suspicion = "TR1", "Benign"
    elif points == 2:
        category, suspicion = "TR2", "Not suspicious"
    elif points == 3:
        category, suspicion = "TR3", "Mildly suspicious"
    elif 4 <= points <= 6:
        category, suspicion = "TR4", "Moderately suspicious"
    elif points >= 7:
        category, suspicion = "TR5", "Highly suspicious"
    else:
        raise ValueError("Impossible ACR TI-RADS score: check descriptors")

    follow_up_cm = None
    fna_cm = None
    follow_up_years = []
    if category in THRESHOLDS_CM:
        follow_up_cm, fna_cm = THRESHOLDS_CM[category]
        if size_cm >= fna_cm:
            action = "FNA threshold met"
        elif size_cm >= follow_up_cm:
            action = "Ultrasound follow-up threshold met"
            follow_up_years = FOLLOWUP_YEARS[category]
        else:
            action = "No routine FNA or follow-up by size criteria"
    else:
        action = "No routine FNA or follow-up by ACR TI-RADS"

    return {
        "points": points,
        "category": category,
        "suspicion": suspicion,
        "component_points": components,
        "size_cm": size_cm,
        "management": action,
        "fna_threshold_cm": fna_cm,
        "followup_threshold_cm": follow_up_cm,
        "followup_years": follow_up_years,
        "note": "Decision support for adult nodules only; clinician judgement and clinical context take precedence.",
        "reference": "ACR TI-RADS 2017; DOI 10.1016/j.jacr.2017.01.046",
    }
