#!/usr/bin/env python3
"""
Synthetic data generator for FPLIP -- Fixed & Audited Version (Option 5: Hybrid).

Produces sample data matching the Source Data Contract for all sources:
  - Transactional: production, downtime, QC
  - Master: machines, products, shifts, downtime_reasons, defect_types
  - Includes a deliberately malformed record for failure-path testing.

AUDIT FIXES APPLIED
-------------------
  1. Product ID Foreign Key Resolution (100 % Match)
     - generate_product_master now creates exact entries for all 20 PRODUCT_IDS
       (P-BLOCK-01..10, P-PAVE-01..05, P-ZEL-01..05).
     - Production runs reference only existing Product Master IDs.

  2. QC Inspection Log Reference Resolution (~65 % Match)
     - generate_qc_sample receives the generated production run records and
       links production_run_reference to actual log_reference_number values.

  3. Timezone-Aware Timestamps (+01:00 Africa/Casablanca)
     - All timestamp fields across all tables include explicit +01:00 offset.

  4. Microsecond Precision Stripped
     - Timestamps are formatted to the second (microsecond=0) to mimic
       manual/system log entry precision cleanly.

  5. Machine Master Naming & Type Collision Fixed
     - All 10 machines (M01..M10) have unique names and matching profiles.

  6. Synthetic Name Artifacts Removed
     - Product catalog expanded so all 20 products have unique, authentic names
       without any "(Variant N)" fallback text.
"""

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from faker import Faker

fake = Faker()

# Seed for NumPy RNG.  None = fresh seed each run (variety).
# Set an integer (e.g. 42) to get fully reproducible output.
_RNG = np.random.default_rng(seed=None)

# Timezone for FPLIP operations: Africa/Casablanca (UTC+1, no DST)
TZ_CASABLANCA = timezone(timedelta(hours=1))


def format_iso_timestamp(dt):
    """
    Format a datetime object as a timezone-aware ISO 8601 string (+01:00),
    with microseconds stripped to 0 for clean manual/system entry display.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    dt_clean = dt.replace(microsecond=0)
    if dt_clean.tzinfo is None:
        dt_clean = dt_clean.replace(tzinfo=TZ_CASABLANCA)
    return dt_clean.isoformat()


# ===========================================================================
# SECTION 1 -- CONSTANTS  (from Source Data Contract -- UNCHANGED from v1)
# ===========================================================================

MACHINE_IDS = [f"M{i:02d}" for i in range(1, 11)]

MACHINE_NAMES = [
    "Vibro-Compactor Line 1",
    "Vibro-Compactor Line 2",
    "Tile Press 1",
    "Tile Press 2",
    "Mixer 1",
    "Mixer 2",
    "Curing Chamber 1",
    "Curing Chamber 2",
    "Mixer 3",
    "Vibro-Compactor Line 3",
]

MACHINE_TYPES = ["Block Press", "Tile Press", "Mixer", "Curing Chamber", "Other"]
MACHINE_STATUSES = ["Active", "Inactive", "Maintenance", "Decommissioned"]
LINE_IDS = ["L1", "L2", "L3"]

PRODUCT_IDS = (
    [f"P-BLOCK-{i:02d}" for i in range(1, 11)]
    + [f"P-PAVE-{i:02d}" for i in range(1, 6)]
    + [f"P-ZEL-{i:02d}" for i in range(1, 6)]
)
PRODUCT_FAMILIES = ["Concrete Block", "Pavement Block", "Zellige", "Other"]
UNITS = ["unit", "m2", "piece"]
CYCLE_TIME_SOURCES = [
    "Manufacturer Spec",
    "Manufacturing Engineering Estimate",
    "Historical Average",
    "Unconfirmed",
]
CONFIDENCE_LEVELS = ["verified", "estimated", "unconfirmed"]

SHIFTS = [
    {
        "shift_id": "S1",
        "shift_name": "Morning",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "crosses_midnight": False,
        "start_hour": 6,
        "duration_hours": 8.0,
    },
    {
        "shift_id": "S2",
        "shift_name": "Afternoon",
        "start_time": "14:00:00",
        "end_time": "22:00:00",
        "crosses_midnight": False,
        "start_hour": 14,
        "duration_hours": 8.0,
    },
    {
        "shift_id": "S3",
        "shift_name": "Night",
        "start_time": "22:00:00",
        "end_time": "06:00:00",
        "crosses_midnight": True,
        "start_hour": 22,
        "duration_hours": 8.0,
    },
]
SHIFT_NAMES = ["Morning", "Afternoon", "Night"]

REASONS = [
    # Index 0
    {
        "reason_id": "DT-CHG-01",
        "reason_name": "Product Changeover",
        "reason_category": "Changeover",
        "oee_loss_category": "Availability Loss",
    },
    # Index 1
    {
        "reason_id": "DT-CHG-02",
        "reason_name": "Mold Changeover",
        "reason_category": "Changeover",
        "oee_loss_category": "Availability Loss",
    },
    # Index 2
    {
        "reason_id": "DT-MAINT-01",
        "reason_name": "Scheduled Maintenance",
        "reason_category": "Maintenance",
        "oee_loss_category": "Availability Loss",
    },
    # Index 3
    {
        "reason_id": "DT-MAINT-02",
        "reason_name": "Emergency Repair",
        "reason_category": "Unplanned",
        "oee_loss_category": "Availability Loss",
    },
    # Index 4
    {
        "reason_id": "DT-MAT-01",
        "reason_name": "Material Shortage",
        "reason_category": "Material Shortage",
        "oee_loss_category": "Availability Loss",
    },
    # Index 5
    {
        "reason_id": "DT-UNPL-01",
        "reason_name": "Power Outage",
        "reason_category": "Unplanned",
        "oee_loss_category": "Availability Loss",
    },
    # Index 6
    {
        "reason_id": "DT-UNPL-02",
        "reason_name": "Operator Unavailable",
        "reason_category": "Unplanned",
        "oee_loss_category": "Availability Loss",
    },
    # Index 7
    {
        "reason_id": "DT-SET-01",
        "reason_name": "Setup/Adjustment",
        "reason_category": "Planned",
        "oee_loss_category": "Availability Loss",
    },
    # Index 8
    {
        "reason_id": "DT-SLOW-01",
        "reason_name": "Slow Running (Minor Stop)",
        "reason_category": "Unplanned",
        "oee_loss_category": "Performance Loss",
    },
    # Index 9
    {
        "reason_id": "DT-OTHER-01",
        "reason_name": "Other",
        "reason_category": "Other",
        "oee_loss_category": "Not Applicable",
    },
]
REASON_CATEGORIES = [
    "Planned",
    "Unplanned",
    "Changeover",
    "Maintenance",
    "Material Shortage",
    "Other",
]
OEE_LOSS_CATEGORIES = ["Availability Loss", "Performance Loss", "Not Applicable"]

DEFECT_TYPES = [
    {
        "defect_type_id": "DEF-DIM-01",
        "defect_name": "Dimension Out of Spec",
        "defect_category": "Dimensional",
        "severity": "Major",
    },
    {
        "defect_type_id": "DEF-VIS-01",
        "defect_name": "Surface Crack",
        "defect_category": "Visual",
        "severity": "Major",
    },
    {
        "defect_type_id": "DEF-VIS-02",
        "defect_name": "Surface Chipping",
        "defect_category": "Visual",
        "severity": "Minor",
    },
    {
        "defect_type_id": "DEF-STRUCT-01",
        "defect_name": "Structural Weakness",
        "defect_category": "Structural",
        "severity": "Critical",
    },
    {
        "defect_type_id": "DEF-MAT-01",
        "defect_name": "Material Inconsistency",
        "defect_category": "Material",
        "severity": "Major",
    },
    {
        "defect_type_id": "DEF-DIM-02",
        "defect_name": "Thickness Variation",
        "defect_category": "Dimensional",
        "severity": "Minor",
    },
    {
        "defect_type_id": "DEF-VIS-03",
        "defect_name": "Color Variation",
        "defect_category": "Visual",
        "severity": "Minor",
    },
    {
        "defect_type_id": "DEF-STRUCT-02",
        "defect_name": "Cracking Under Load",
        "defect_category": "Structural",
        "severity": "Critical",
    },
    {
        "defect_type_id": "DEF-MAT-02",
        "defect_name": "Surface Porosity",
        "defect_category": "Material",
        "severity": "Minor",
    },
    {
        "defect_type_id": "DEF-OTHER-01",
        "defect_name": "Other Defect",
        "defect_category": "Other",
        "severity": "Minor",
    },
]
DEFECT_CATEGORIES = ["Dimensional", "Visual", "Structural", "Material", "Other"]
SEVERITIES = ["Minor", "Major", "Critical"]
DATA_ENTRY_METHODS = ["Manual", "ERP Export", "Machine Export"]


# ===========================================================================
# SECTION 2 -- ENHANCED: MACHINE PERFORMANCE PROFILES (10 Machines)
# ===========================================================================

MACHINE_PROFILES = {
    "M01": {
        "machine_name": "Vibro-Compactor Line 1",
        "machine_type": "Block Press",
        "line_id": "L1",
        "manufacturer": "Masa Group",
        "nominal_units_per_hour": 450,
        "run_cv": 0.07,
        "defect_alpha": 2.0,
        "defect_beta": 98.0,
        "downtime_lambda": 2.5,
        "dt_weibull_shape": 0.75,
        "dt_weibull_scale_sec": 360,
        "post_repair_protection_hr": 3.0,
        "compatible_products": ["Concrete Block"],
        "reason_weights": [0.28, 0.22, 0.08, 0.09, 0.08, 0.03, 0.04, 0.10, 0.06, 0.02],
    },
    "M02": {
        "machine_name": "Vibro-Compactor Line 2",
        "machine_type": "Block Press",
        "line_id": "L1",
        "manufacturer": "Hess",
        "nominal_units_per_hour": 415,
        "run_cv": 0.09,
        "defect_alpha": 3.0,
        "defect_beta": 97.0,
        "downtime_lambda": 3.2,
        "dt_weibull_shape": 0.78,
        "dt_weibull_scale_sec": 420,
        "post_repair_protection_hr": 2.5,
        "compatible_products": ["Concrete Block"],
        "reason_weights": [0.25, 0.20, 0.09, 0.13, 0.09, 0.03, 0.05, 0.09, 0.06, 0.01],
    },
    "M03": {
        "machine_name": "Tile Press 1",
        "machine_type": "Tile Press",
        "line_id": "L2",
        "manufacturer": "KVM",
        "nominal_units_per_hour": 300,
        "run_cv": 0.10,
        "defect_alpha": 4.5,
        "defect_beta": 95.5,
        "downtime_lambda": 4.2,
        "dt_weibull_shape": 0.80,
        "dt_weibull_scale_sec": 480,
        "post_repair_protection_hr": 2.0,
        "compatible_products": ["Pavement Block", "Zellige"],
        "reason_weights": [0.14, 0.30, 0.10, 0.12, 0.08, 0.03, 0.05, 0.10, 0.06, 0.02],
    },
    "M04": {
        "machine_name": "Tile Press 2",
        "machine_type": "Tile Press",
        "line_id": "L2",
        "manufacturer": "KVM",
        "nominal_units_per_hour": 270,
        "run_cv": 0.12,
        "defect_alpha": 5.5,
        "defect_beta": 94.5,
        "downtime_lambda": 4.8,
        "dt_weibull_shape": 0.82,
        "dt_weibull_scale_sec": 540,
        "post_repair_protection_hr": 2.0,
        "compatible_products": ["Pavement Block", "Zellige"],
        "reason_weights": [0.12, 0.28, 0.10, 0.14, 0.10, 0.03, 0.06, 0.10, 0.05, 0.02],
    },
    "M05": {
        "machine_name": "Mixer 1",
        "machine_type": "Mixer",
        "line_id": "L3",
        "manufacturer": "Sicoma",
        "nominal_units_per_hour": 200,
        "run_cv": 0.15,
        "defect_alpha": 6.0,
        "defect_beta": 94.0,
        "downtime_lambda": 2.2,
        "dt_weibull_shape": 0.85,
        "dt_weibull_scale_sec": 660,
        "post_repair_protection_hr": 4.0,
        "compatible_products": ["Concrete Block", "Pavement Block"],
        "reason_weights": [0.05, 0.05, 0.12, 0.10, 0.36, 0.05, 0.08, 0.12, 0.05, 0.02],
    },
    "M06": {
        "machine_name": "Mixer 2",
        "machine_type": "Mixer",
        "line_id": "L3",
        "manufacturer": "Elba",
        "nominal_units_per_hour": 185,
        "run_cv": 0.16,
        "defect_alpha": 7.0,
        "defect_beta": 93.0,
        "downtime_lambda": 2.7,
        "dt_weibull_shape": 0.85,
        "dt_weibull_scale_sec": 720,
        "post_repair_protection_hr": 4.0,
        "compatible_products": ["Concrete Block", "Pavement Block"],
        "reason_weights": [0.04, 0.04, 0.12, 0.11, 0.38, 0.05, 0.08, 0.12, 0.04, 0.02],
    },
    "M07": {
        "machine_name": "Curing Chamber 1",
        "machine_type": "Curing Chamber",
        "line_id": "L1",
        "manufacturer": "Masa Group",
        "nominal_units_per_hour": 120,
        "run_cv": 0.05,
        "defect_alpha": 1.0,
        "defect_beta": 99.0,
        "downtime_lambda": 0.8,
        "dt_weibull_shape": 1.0,
        "dt_weibull_scale_sec": 1080,
        "post_repair_protection_hr": 6.0,
        "compatible_products": ["Concrete Block", "Pavement Block", "Zellige"],
        "reason_weights": [0.05, 0.04, 0.40, 0.20, 0.05, 0.08, 0.03, 0.10, 0.02, 0.03],
    },
    "M08": {
        "machine_name": "Curing Chamber 2",
        "machine_type": "Curing Chamber",
        "line_id": "L2",
        "manufacturer": "Hess",
        "nominal_units_per_hour": 108,
        "run_cv": 0.06,
        "defect_alpha": 1.5,
        "defect_beta": 98.5,
        "downtime_lambda": 1.0,
        "dt_weibull_shape": 1.0,
        "dt_weibull_scale_sec": 1200,
        "post_repair_protection_hr": 6.0,
        "compatible_products": ["Concrete Block", "Pavement Block", "Zellige"],
        "reason_weights": [0.04, 0.04, 0.42, 0.20, 0.05, 0.08, 0.03, 0.10, 0.02, 0.02],
    },
    "M09": {
        "machine_name": "Mixer 3",
        "machine_type": "Mixer",
        "line_id": "L3",
        "manufacturer": "Sicoma",
        "nominal_units_per_hour": 190,
        "run_cv": 0.15,
        "defect_alpha": 6.5,
        "defect_beta": 93.5,
        "downtime_lambda": 2.5,
        "dt_weibull_shape": 0.85,
        "dt_weibull_scale_sec": 700,
        "post_repair_protection_hr": 4.0,
        "compatible_products": ["Concrete Block", "Pavement Block"],
        "reason_weights": [0.04, 0.04, 0.12, 0.11, 0.38, 0.05, 0.08, 0.12, 0.04, 0.02],
    },
    "M10": {
        "machine_name": "Vibro-Compactor Line 3",
        "machine_type": "Block Press",
        "line_id": "L1",
        "manufacturer": "Besser",
        "nominal_units_per_hour": 400,
        "run_cv": 0.08,
        "defect_alpha": 2.5,
        "defect_beta": 97.5,
        "downtime_lambda": 3.0,
        "dt_weibull_shape": 0.76,
        "dt_weibull_scale_sec": 400,
        "post_repair_protection_hr": 3.0,
        "compatible_products": ["Concrete Block"],
        "reason_weights": [0.26, 0.21, 0.08, 0.11, 0.08, 0.03, 0.05, 0.10, 0.06, 0.02],
    },
}


# ===========================================================================
# SECTION 3 -- ENHANCED: SHIFT MODIFIERS
# ===========================================================================

SHIFT_MODIFIERS = {
    "S1": {
        "output_factor": 1.00,
        "quality_degradation_factor": 1.00,
        "downtime_scale_factor": 1.00,
        "mapped_reason_pct": 0.80,
    },
    "S2": {
        "output_factor": 0.97,
        "quality_degradation_factor": 1.05,
        "downtime_scale_factor": 1.15,
        "mapped_reason_pct": 0.75,
    },
    "S3": {
        "output_factor": 0.92,
        "quality_degradation_factor": 1.20,
        "downtime_scale_factor": 1.40,
        "mapped_reason_pct": 0.60,
    },
}


# ===========================================================================
# SECTION 4 -- ENHANCED: MACHINE-TYPE DEFECT AFFINITIES
# ===========================================================================

MACHINE_DEFECT_WEIGHTS = {
    "Block Press": [
        0.25,  # DEF-DIM-01 Dimension Out of Spec
        0.20,  # DEF-VIS-01 Surface Crack
        0.18,  # DEF-VIS-02 Surface Chipping
        0.08,  # DEF-STRUCT-01 Structural Weakness
        0.08,  # DEF-MAT-01 Material Inconsistency
        0.08,  # DEF-DIM-02 Thickness Variation
        0.05,  # DEF-VIS-03 Color Variation
        0.03,  # DEF-STRUCT-02 Cracking Under Load
        0.04,  # DEF-MAT-02 Surface Porosity
        0.01,  # DEF-OTHER-01
    ],
    "Tile Press": [
        0.20,  # DEF-DIM-01
        0.10,  # DEF-VIS-01
        0.15,  # DEF-VIS-02
        0.05,  # DEF-STRUCT-01
        0.07,  # DEF-MAT-01
        0.22,  # DEF-DIM-02 Thickness Variation
        0.13,  # DEF-VIS-03 Color Variation
        0.03,  # DEF-STRUCT-02
        0.04,  # DEF-MAT-02
        0.01,  # DEF-OTHER-01
    ],
    "Mixer": [
        0.04,  # DEF-DIM-01
        0.04,  # DEF-VIS-01
        0.04,  # DEF-VIS-02
        0.10,  # DEF-STRUCT-01
        0.42,  # DEF-MAT-01 Material Inconsistency
        0.04,  # DEF-DIM-02
        0.05,  # DEF-VIS-03
        0.12,  # DEF-STRUCT-02
        0.13,  # DEF-MAT-02 Surface Porosity
        0.02,  # DEF-OTHER-01
    ],
    "Curing Chamber": [
        0.04,  # DEF-DIM-01
        0.08,  # DEF-VIS-01
        0.05,  # DEF-VIS-02
        0.28,  # DEF-STRUCT-01 Structural Weakness
        0.08,  # DEF-MAT-01
        0.04,  # DEF-DIM-02
        0.03,  # DEF-VIS-03
        0.28,  # DEF-STRUCT-02 Cracking Under Load
        0.10,  # DEF-MAT-02
        0.02,  # DEF-OTHER-01
    ],
    "Other": [0.10] * 10,
}


# ===========================================================================
# SECTION 5 -- ENHANCED: DOMAIN-ACCURATE PRODUCT CATALOG
# ===========================================================================

# 10 Concrete Block + 5 Pavement Block + 5 Zellige = 20 unique product names
PRODUCT_NAMES_BY_FAMILY = {
    "Concrete Block": [
        "Hollow Block 20x20x40 cm",
        "Hollow Block 15x20x40 cm",
        "Hollow Block 10x20x40 cm",
        "Solid Block 20x20x40 cm",
        "Solid Block 15x20x40 cm",
        "Half Block 20x20x20 cm",
        "Column Block 20x30x20 cm",
        "Lintel Block 20x20x40 cm",
        "Foundation Block 20x30x40 cm",
        "Insulation Block 20x20x40 cm",
    ],
    "Pavement Block": [
        "Holland Paver 10x20x6 cm",
        "Holland Paver 10x20x8 cm",
        "Tumbled Paver 20x10x6 cm",
        "Curbstone Standard 100x15x30 cm",
        "Curbstone Lowered 100x12x25 cm",
    ],
    "Zellige": [
        "Zellige White 10x10x1.2 cm",
        "Zellige Blue 10x10x1.2 cm",
        "Zellige Green 10x10x1.2 cm",
        "Zellige Terracotta 10x10x1.2 cm",
        "Zellige Mosaic 5x5x1.2 cm",
    ],
    "Other": [
        "Custom Precast Element",
        "Drainage Channel Block",
        "Retaining Wall Block 20x25x40 cm",
        "Garden Border Block 8x8x30 cm",
    ],
}

FAMILY_CYCLE_TIMES = {
    "Concrete Block": (12.0, 1.5, 8.0, 18.0),
    "Pavement Block": (18.0, 2.5, 10.0, 28.0),
    "Zellige": (42.0, 5.0, 30.0, 60.0),
    "Other": (25.0, 4.0, 15.0, 45.0),
}

FAMILY_WEIGHT_RANGES = {
    "Concrete Block": (8.0, 22.0),
    "Pavement Block": (2.5, 12.0),
    "Zellige": (0.15, 0.50),
    "Other": (5.0, 35.0),
}

MACHINE_MANUFACTURERS = {
    "Block Press": ["Masa Group", "Hess", "Besser", "Columbia Machine"],
    "Tile Press": ["KVM", "Omag", "S+R Manus", "Masa Group"],
    "Mixer": ["Sicoma", "Elba", "Pan-Americana", "Wacker Neuson"],
    "Curing Chamber": ["Masa Group", "Hess", "Labomat", "Custom Fabrication"],
    "Other": ["Generic OEM", "Custom Fabrication"],
}

PRODUCTION_NOTES_TEMPLATES = [
    "Slow start, mold warm-up required.",
    "Minor vibration detected, adjusted.",
    "Batch ran smoothly.",
    "Mix slightly dry, adjusted water ratio.",
    "Mold cleaned mid-run.",
    "Speed reduced after sensor trip.",
    "Good run, no issues.",
    "End of shift -- incomplete run.",
    "First run after changeover.",
    "Material slightly coarser than spec.",
]


# ===========================================================================
# SECTION 6 -- PRIVATE HELPER FUNCTIONS
# ===========================================================================


def _temporal_drift(target_date):
    day = max(1, min(31, target_date.day))
    return 1.0 + (day - 1) / 30.0 * 0.08


def _output_drift(target_date):
    day = max(1, min(31, target_date.day))
    return 1.0 - (day - 1) / 30.0 * 0.04


def _sample_run_duration_hours():
    mu = np.log(2.0)
    sigma = 0.55
    hours = float(_RNG.lognormal(mean=mu, sigma=sigma))
    return max(0.25, min(7.0, hours))


def _sample_produced_units(machine_id, shift_id, run_hours, target_date):
    p = MACHINE_PROFILES[machine_id]
    s = SHIFT_MODIFIERS[shift_id]
    expected = (
        p["nominal_units_per_hour"]
        * run_hours
        * s["output_factor"]
        * _output_drift(target_date)
    )
    std = expected * p["run_cv"]
    produced = int(max(0.0, float(_RNG.normal(expected, std))))
    return produced


def _sample_defect_rate(machine_id, shift_id, target_date):
    p = MACHINE_PROFILES[machine_id]
    base_rate = float(_RNG.beta(p["defect_alpha"], p["defect_beta"]))
    degraded = base_rate * SHIFT_MODIFIERS[shift_id]["quality_degradation_factor"]
    degraded = degraded * _temporal_drift(target_date)
    return max(0.0, min(0.40, degraded))


def _sample_downtime_duration_sec(machine_id):
    p = MACHINE_PROFILES[machine_id]
    raw = float(_RNG.weibull(p["dt_weibull_shape"])) * p["dt_weibull_scale_sec"]
    return int(max(30, min(14400, raw)))


def _n_downtime_events(machine_id, shift_id, target_date):
    p = MACHINE_PROFILES[machine_id]
    lam = (
        p["downtime_lambda"]
        * SHIFT_MODIFIERS[shift_id]["downtime_scale_factor"]
        * _temporal_drift(target_date)
    )
    return int(_RNG.poisson(lam))


def _pick_reason(machine_id, shift_id, recent_emergency_repair=False):
    weights = list(MACHINE_PROFILES[machine_id]["reason_weights"])
    if recent_emergency_repair:
        weights[3] *= 0.20
    total = sum(weights)
    norm = [w / total for w in weights]
    idx = int(_RNG.choice(len(REASONS), p=norm))
    return REASONS[idx]


def _pick_defect_type(machine_id):
    mtype = MACHINE_PROFILES[machine_id]["machine_type"]
    weights = MACHINE_DEFECT_WEIGHTS.get(mtype, MACHINE_DEFECT_WEIGHTS["Other"])
    total = sum(weights)
    norm = [w / total for w in weights]
    idx = int(_RNG.choice(len(DEFECT_TYPES), p=norm))
    return DEFECT_TYPES[idx]


def _compatible_products(machine_id, valid_product_ids=None):
    families = MACHINE_PROFILES[machine_id]["compatible_products"]
    family_to_prefix = {
        "Concrete Block": "P-BLOCK-",
        "Pavement Block": "P-PAVE-",
        "Zellige": "P-ZEL-",
    }
    pool = valid_product_ids if valid_product_ids else PRODUCT_IDS
    result = []
    for fam in families:
        prefix = family_to_prefix.get(fam)
        if prefix:
            result.extend(pid for pid in pool if pid.startswith(prefix))
    return result or pool


def _shift_start_dt(target_date, shift):
    base = datetime.combine(target_date, datetime.min.time())
    return base.replace(hour=shift["start_hour"], minute=0, second=0)


def _free_text_for_reason(reason):
    templates = {
        "DT-CHG-01": [
            "changing product spec",
            "switched to different block size",
            "product change, adjusting machine",
        ],
        "DT-CHG-02": [
            "mold swap",
            "changed mold set no. 3",
            "mold replacement",
        ],
        "DT-MAINT-01": [
            "monthly PM",
            "scheduled service",
            "planned oil change",
        ],
        "DT-MAINT-02": [
            "breakdown",
            "machine stopped, called maintenance",
            "hydraulic failure",
            "belt snapped",
            "vibration unit fault",
        ],
        "DT-MAT-01": [
            "waiting for cement delivery",
            "aggregate bin empty",
            "no mix available",
            "material out",
        ],
        "DT-UNPL-01": [
            "power cut",
            "electricity off",
            "circuit breaker tripped",
        ],
        "DT-UNPL-02": [
            "operator absent",
            "waiting for operator",
            "shift handover delayed",
        ],
        "DT-SET-01": [
            "setup adjustment",
            "calibration",
            "tolerance out -- adjusting",
        ],
        "DT-SLOW-01": [
            "running slow",
            "minor jams",
            "machine not at full speed",
        ],
        "DT-OTHER-01": [
            "other",
            "not specified",
            "miscellaneous stop",
        ],
    }
    pool = templates.get(reason["reason_id"], ["stop -- reason unknown"])
    return random.choice(pool)


# ===========================================================================
# SECTION 7 -- FIELD HELPER FUNCTIONS (UNCHANGED from v1)
# ===========================================================================


def get_machine_fields():
    return [
        "machine_id",
        "machine_name",
        "machine_type",
        "line_id",
        "location",
        "manufacturer",
        "install_date",
        "status",
        "nominal_capacity_units_per_hour",
        "data_entry_method",
        "last_updated_at",
        "last_updated_by",
    ]


def get_product_fields():
    return [
        "product_id",
        "product_name",
        "product_family",
        "unit_of_measure",
        "standard_cycle_time_sec",
        "cycle_time_source",
        "cycle_time_confidence",
        "standard_weight_kg",
        "active_flag",
        "data_entry_method",
        "created_at",
        "last_updated_at",
    ]


def get_shift_fields():
    return [
        "shift_id",
        "shift_name",
        "start_time",
        "end_time",
        "crosses_midnight",
        "active_flag",
    ]


def get_downtime_reason_fields():
    return [
        "reason_id",
        "reason_name",
        "reason_category",
        "oee_loss_category",
        "description",
        "active_flag",
    ]


def get_defect_type_fields():
    return [
        "defect_type_id",
        "defect_name",
        "defect_category",
        "severity",
        "description",
        "active_flag",
    ]


# ===========================================================================
# SECTION 8 -- MASTER DATA GENERATORS (Fixed & 100% Unique)
# ===========================================================================


def generate_machine_master(count=10):
    """
    Generate Machine Master data (M01..M10).
    """
    rows = []
    for i in range(1, count + 1):
        machine_id = f"M{i:02d}"
        profile = MACHINE_PROFILES.get(machine_id)

        if profile:
            mtype = profile["machine_type"]
            mname = profile["machine_name"]
            line = profile["line_id"]
            mfr = profile["manufacturer"]
            capacity = profile["nominal_units_per_hour"]
        else:
            mtype = random.choice(MACHINE_TYPES)
            mname = f"Auxiliary Machine {i}"
            line = random.choice(LINE_IDS) if random.random() > 0.3 else None
            mfr = random.choice(
                MACHINE_MANUFACTURERS.get(mtype, MACHINE_MANUFACTURERS["Other"])
            ) if random.random() > 0.4 else None
            capacity = random.choice([200, 300, 450, 600, 800])

        location = (
            f"Building {random.choice(['A', 'B', 'C'])} - Bay {random.randint(1, 5)}"
            if random.random() > 0.25
            else None
        )
        status_weights = [0.78, 0.05, 0.12, 0.05]
        status = random.choices(MACHINE_STATUSES, weights=status_weights)[0]

        updated = fake.date_time_between(start_date="-30d", end_date="now")

        rows.append(
            {
                "machine_id": machine_id,
                "machine_name": mname,
                "machine_type": mtype,
                "line_id": line,
                "location": location,
                "manufacturer": mfr if random.random() > 0.15 else None,
                "install_date": fake.date_between(
                    start_date="-6y", end_date="-1y"
                ).isoformat()
                if random.random() > 0.1
                else None,
                "status": status,
                "nominal_capacity_units_per_hour": capacity
                if random.random() > 0.2
                else None,
                "data_entry_method": random.choice(["Manual", "ERP Export"]),
                "last_updated_at": format_iso_timestamp(updated),
                "last_updated_by": f"EMP-{random.randint(100, 999):04d}"
                if random.random() > 0.25
                else None,
            }
        )
    return rows


def generate_product_master(count=20):
    """
    Generate Product Master data matching PRODUCT_IDS contract exactly.
    Creates entries for all 20 PRODUCT_IDS (P-BLOCK-01..10, P-PAVE-01..05, P-ZEL-01..05).
    """
    rows = []
    # Build list of product specs matching PRODUCT_IDS
    product_specs = []
    for pid in PRODUCT_IDS:
        if "BLOCK" in pid:
            family = "Concrete Block"
        elif "PAVE" in pid:
            family = "Pavement Block"
        elif "ZEL" in pid:
            family = "Zellige"
        else:
            family = "Other"
        product_specs.append((pid, family))

    family_counters = {"Concrete Block": 0, "Pavement Block": 0, "Zellige": 0, "Other": 0}

    for product_id, family in product_specs[:count]:
        idx = family_counters[family]
        family_counters[family] += 1

        pool = PRODUCT_NAMES_BY_FAMILY.get(family, ["Custom Product"])
        name = pool[idx % len(pool)]

        ct_mean, ct_std, ct_min, ct_max = FAMILY_CYCLE_TIMES[family]
        cycle_time = round(
            max(ct_min, min(ct_max, float(_RNG.normal(ct_mean, ct_std)))), 2
        )

        wlo, whi = FAMILY_WEIGHT_RANGES[family]
        weight = round(random.uniform(wlo, whi), 2) if random.random() > 0.2 else None

        confidence = random.choices(
            CONFIDENCE_LEVELS, weights=[0.35, 0.45, 0.20]
        )[0]
        if confidence == "verified":
            source = random.choice(
                [s for s in CYCLE_TIME_SOURCES if s != "Unconfirmed"]
            )
        else:
            source = random.choice(CYCLE_TIME_SOURCES)

        active = random.random() > 0.12

        created = fake.date_time_between(start_date="-3y", end_date="-6m")
        updated = fake.date_time_between(start_date=created, end_date="now")

        rows.append(
            {
                "product_id": product_id,
                "product_name": name,
                "product_family": family,
                "unit_of_measure": {
                    "Concrete Block": "unit",
                    "Pavement Block": "unit",
                    "Zellige": "m2",
                    "Other": "piece",
                }[family],
                "standard_cycle_time_sec": cycle_time,
                "cycle_time_source": source,
                "cycle_time_confidence": confidence,
                "standard_weight_kg": weight,
                "active_flag": active,
                "data_entry_method": random.choice(["Manual", "ERP Export"]),
                "created_at": format_iso_timestamp(created),
                "last_updated_at": format_iso_timestamp(updated),
            }
        )
    return rows


def generate_shift_master():
    return [
        {
            "shift_id": "S1",
            "shift_name": "Morning",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
            "crosses_midnight": False,
            "active_flag": True,
        },
        {
            "shift_id": "S2",
            "shift_name": "Afternoon",
            "start_time": "14:00:00",
            "end_time": "22:00:00",
            "crosses_midnight": False,
            "active_flag": True,
        },
        {
            "shift_id": "S3",
            "shift_name": "Night",
            "start_time": "22:00:00",
            "end_time": "06:00:00",
            "crosses_midnight": True,
            "active_flag": True,
        },
    ]


def generate_downtime_reason_master():
    descriptions = {
        "DT-CHG-01": "Time to switch from one product specification to another, including parameter adjustment on the press.",
        "DT-CHG-02": "Physical mold swap on the press; includes unmounting, cleaning, and re-mounting the new mold set.",
        "DT-MAINT-01": "Planned preventive maintenance window per the monthly maintenance schedule.",
        "DT-MAINT-02": "Unplanned corrective repair; machine stopped due to mechanical or electrical failure.",
        "DT-MAT-01": "Production halted because cement, aggregate, or additive stock ran out before replenishment.",
        "DT-UNPL-01": "Site-level power outage or breaker trip; production halted until power restored.",
        "DT-UNPL-02": "Operator absent, late, or reassigned; machine idle pending replacement.",
        "DT-SET-01": "Machine or mold adjustment required to bring output back within dimensional tolerance.",
        "DT-SLOW-01": "Machine running below ideal cycle rate (minor recurring stoppages < 5 min each, not logged individually).",
        "DT-OTHER-01": "Stop reason does not fit any other category; to be reviewed for reclassification.",
    }
    rows = []
    for r in REASONS:
        rows.append(
            {
                "reason_id": r["reason_id"],
                "reason_name": r["reason_name"],
                "reason_category": r["reason_category"],
                "oee_loss_category": r["oee_loss_category"],
                "description": descriptions.get(r["reason_id"]),
                "active_flag": True,
            }
        )
    return rows


def generate_defect_type_master():
    descriptions = {
        "DEF-DIM-01": "Any block dimension outside +/-2 mm tolerance per NM 10.1.008 section 6.1.",
        "DEF-VIS-01": "Surface crack visible to the naked eye exceeding 0.2 mm width or 25 mm length.",
        "DEF-VIS-02": "Corner or edge chipping deeper than 3 mm or longer than 15 mm.",
        "DEF-STRUCT-01": "Block fails compressive strength test below 7.5 N/mm2 (standard grade).",
        "DEF-MAT-01": "Visual or physical evidence of uneven aggregate distribution or voids.",
        "DEF-DIM-02": "Block thickness varies > 1.5 mm between two opposite faces.",
        "DEF-VIS-03": "Unacceptable color mismatch versus the approved reference tile (delta E > 3.0).",
        "DEF-STRUCT-02": "Block fractures under simulated service load before reaching rated strength.",
        "DEF-MAT-02": "Surface shows open pores larger than 1 mm, reducing weather resistance.",
        "DEF-OTHER-01": "Defect not classifiable into the above categories; flagged for QC review.",
    }
    rows = []
    for d in DEFECT_TYPES:
        rows.append(
            {
                "defect_type_id": d["defect_type_id"],
                "defect_name": d["defect_name"],
                "defect_category": d["defect_category"],
                "severity": d["severity"],
                "description": descriptions.get(d["defect_type_id"]),
                "active_flag": True,
            }
        )
    return rows


# ===========================================================================
# SECTION 9 -- TRANSACTIONAL DATA GENERATORS
# ===========================================================================


def generate_production_sample(target_date=None, num_rows=50, valid_product_ids=None, machine_rows=None):
    """
    Generate Production Run Log data.
    Ensures 100 % of product_id values exist in Product Master.
    Ensures 100 % of timestamps are timezone-aware (+01:00).
    Selection probability is weighted by machine status in Machine Master:
      - Active: 1.0 (normal production)
      - Maintenance: 0.15 (short run before stopping for service)
      - Inactive / Decommissioned: 0.0 (no production)
    """
    if target_date is None:
        target_date = datetime.now().date()

    if valid_product_ids is None:
        valid_product_ids = PRODUCT_IDS

    # Machine status weighting
    status_map = {m["machine_id"]: m["status"] for m in machine_rows} if machine_rows else {}
    machine_weights = []
    for mid in MACHINE_IDS:
        st = status_map.get(mid, "Active")
        if st == "Active":
            w = 1.0
        elif st == "Maintenance":
            w = 0.15
        else:
            w = 0.0
        machine_weights.append(w)

    total_w = sum(machine_weights)
    if total_w > 0:
        machine_p = [w / total_w for w in machine_weights]
    else:
        machine_p = None

    rows = []
    run_seq_counter: dict = {}

    for _ in range(num_rows):
        if machine_p:
            machine_id = random.choices(MACHINE_IDS, weights=machine_p)[0]
        else:
            machine_id = random.choice(MACHINE_IDS)

        shift = random.choice(SHIFTS)
        shift_id = shift["shift_id"]

        # Pick a product compatible with this machine from valid product list
        product_id = random.choice(_compatible_products(machine_id, valid_product_ids))

        # Composite key for run_sequence_number
        key = f"{machine_id}_{shift_id}_{product_id}_{target_date.isoformat()}"
        run_seq_counter[key] = run_seq_counter.get(key, 0) + 1
        seq_num = run_seq_counter[key]

        # Timestamps
        run_hours = _sample_run_duration_hours()

        shift_start = _shift_start_dt(target_date, shift)
        latest_start_offset = max(0.0, shift["duration_hours"] - run_hours) * 0.6
        start_offset_min = int(random.uniform(0, max(1, latest_start_offset * 60)))
        start_time = shift_start + timedelta(minutes=start_offset_min)

        if shift["crosses_midnight"]:
            start_time += timedelta(days=1)

        end_time = start_time + timedelta(hours=run_hours)

        # Volumes
        produced = _sample_produced_units(machine_id, shift_id, run_hours, target_date)
        defect_rate = _sample_defect_rate(machine_id, shift_id, target_date)
        good = int(max(0, min(produced, produced * (1.0 - defect_rate))))

        p = MACHINE_PROFILES[machine_id]
        planned_nominal = int(
            p["nominal_units_per_hour"]
            * run_hours
            * SHIFT_MODIFIERS[shift_id]["output_factor"]
        )
        planned = planned_nominal if random.random() > 0.35 else None

        has_timestamps = random.random() > 0.15
        has_log_ref = random.random() > 0.25

        note = None
        if random.random() > 0.55:
            if defect_rate > 0.06:
                note = random.choice([
                    "High reject rate -- QC called.",
                    "Material batch inconsistency noted.",
                    "Vibration above normal, checked and continued.",
                    "Slow start, quality stabilised after 20 min.",
                ])
            else:
                note = random.choice(PRODUCTION_NOTES_TEMPLATES)

        entry_delay_min = random.randint(5, 90)
        entered_at = end_time + timedelta(minutes=entry_delay_min)

        rows.append(
            {
                "log_reference_number": (
                    f"LOG-{target_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                    if has_log_ref
                    else None
                ),
                "machine_id": machine_id,
                "shift_id": shift_id,
                "product_id": product_id,
                "run_date": target_date.isoformat(),
                "run_sequence_number": seq_num,
                "run_start_time": format_iso_timestamp(start_time) if has_timestamps else None,
                "run_end_time": format_iso_timestamp(end_time) if has_timestamps else None,
                "planned_units": planned,
                "produced_units": produced,
                "good_units": good,
                "operator_id": (
                    f"EMP-{random.randint(100, 999):04d}"
                    if random.random() > 0.25
                    else None
                ),
                "notes": note,
                "data_entry_method": random.choices(
                    ["Manual", "ERP Export", "Machine Export"],
                    weights=[0.55, 0.35, 0.10],
                )[0],
                "entered_by": f"EMP-{random.randint(100, 999):04d}",
                "entered_at": format_iso_timestamp(entered_at),
            }
        )

    return rows


def generate_downtime_sample(target_date=None, num_rows=30):
    """
    Generate Downtime Event Log data.
    Ensures 100 % of timestamps are timezone-aware (+01:00).
    """
    if target_date is None:
        target_date = datetime.now().date()

    rows = []
    event_counter = 1
    last_emergency: dict = {}

    target_per_machine_shift = num_rows / (len(MACHINE_IDS) * len(SHIFTS))
    poisson_scale = max(0.5, target_per_machine_shift / 3.0)

    for shift in SHIFTS:
        shift_id = shift["shift_id"]
        shift_start = _shift_start_dt(target_date, shift)
        if shift["crosses_midnight"]:
            shift_start += timedelta(days=1)

        for machine_id in MACHINE_IDS:
            n_events = _n_downtime_events(machine_id, shift_id, target_date)
            n_events = max(0, int(round(n_events * poisson_scale)))

            shift_seconds = int(shift["duration_hours"] * 3600)
            event_starts = sorted(
                int(random.uniform(0, shift_seconds - 30)) for _ in range(n_events)
            )

            for offset_sec in event_starts:
                event_start = shift_start + timedelta(seconds=offset_sec)

                recent_emergency = False
                if machine_id in last_emergency:
                    hrs_since = (
                        event_start - last_emergency[machine_id]
                    ).total_seconds() / 3600
                    protection = MACHINE_PROFILES[machine_id]["post_repair_protection_hr"]
                    if hrs_since < protection:
                        recent_emergency = True

                duration_sec = _sample_downtime_duration_sec(machine_id)
                end_dt = event_start + timedelta(seconds=duration_sec)

                reason = _pick_reason(machine_id, shift_id, recent_emergency)

                if reason["reason_id"] == "DT-MAINT-02":
                    last_emergency[machine_id] = event_start

                mapped_pct = SHIFT_MODIFIERS[shift_id]["mapped_reason_pct"]
                has_reason_id = random.random() < mapped_pct

                end_recorded = random.random() > 0.05

                if end_recorded:
                    entry_base = end_dt
                else:
                    entry_base = shift_start + timedelta(seconds=shift_seconds)
                entered_at = entry_base + timedelta(minutes=random.randint(5, 45))

                rows.append(
                    {
                        "event_id": (
                            f"DTE-{target_date.strftime('%Y%m%d')}-{event_counter:04d}"
                        ),
                        "machine_id": machine_id,
                        "shift_id": shift_id,
                        "event_date": target_date.isoformat(),
                        "reason_id": reason["reason_id"] if has_reason_id else None,
                        "reason_free_text": (
                            None
                            if has_reason_id
                            else _free_text_for_reason(reason)
                        ),
                        "start_time": format_iso_timestamp(event_start),
                        "end_time": format_iso_timestamp(end_dt) if end_recorded else None,
                        "duration_sec": duration_sec,
                        "data_entry_method": random.choices(
                            ["Manual", "ERP Export"],
                            weights=[0.70, 0.30],
                        )[0],
                        "entered_by": f"EMP-{random.randint(100, 999):04d}",
                        "entered_at": format_iso_timestamp(entered_at),
                    }
                )
                event_counter += 1

    return rows


def generate_qc_sample(target_date=None, num_rows=25, prod_rows=None):
    """
    Generate QC Inspection Log data.
    Links production_run_reference to actual generated production log reference numbers.
    Ensures 100 % of timestamps are timezone-aware (+01:00).
    """
    if target_date is None:
        target_date = datetime.now().date()

    rows = []
    inspection_counter = 1

    # Extract non-null log_reference_number values from generated production runs
    valid_log_refs = []
    if prod_rows:
        valid_log_refs = [
            r["log_reference_number"]
            for r in prod_rows
            if r.get("log_reference_number")
        ]

    inspector_pool = [
        f"EMP-{random.randint(100, 999):04d}" for _ in range(random.randint(2, 4))
    ]

    for _ in range(num_rows):
        machine_id = random.choice(MACHINE_IDS)
        units_inspected = max(10, int(_RNG.normal(loc=55, scale=20)))

        p = MACHINE_PROFILES[machine_id]
        base_defect = float(
            _RNG.beta(p["defect_alpha"] * 0.5, p["defect_beta"] * 0.5)
        )
        base_defect *= _temporal_drift(target_date)
        base_defect = max(0.0, min(0.40, base_defect))

        rejected = int(round(units_inspected * base_defect))
        rejected = max(0, min(rejected, units_inspected))

        defect = _pick_defect_type(machine_id) if rejected > 0 else None

        # Link ~65 % of QC rows to a run reference:
        # Of those with a reference: ~75% resolve to a valid production log_reference_number,
        # while ~25% reference an unresolvable paper log string (e.g. LOG-UNRESOLV-4821).
        # This achieves an overall ~50% resolution rate (matching the contract's 40-70% target).
        has_run_ref = random.random() < 0.65
        if has_run_ref:
            if prod_rows and random.random() < 0.75:
                selected_prod = random.choice(prod_rows)
                production_ref = selected_prod.get("log_reference_number")
                if selected_prod.get("machine_id"):
                    machine_id = selected_prod["machine_id"]
            elif valid_log_refs and random.random() < 0.75:
                production_ref = random.choice(valid_log_refs)
            else:
                production_ref = f"LOG-{target_date.strftime('%Y%m%d')}-UNRESOLV-{random.randint(10, 99)}"
        else:
            production_ref = None

        inspection_hour = random.randint(7, 19)
        entered_at = datetime.combine(target_date, datetime.min.time()).replace(
            hour=inspection_hour, minute=random.randint(0, 59)
        )

        rows.append(
            {
                "inspection_id": (
                    f"QC-{target_date.strftime('%Y%m%d')}-{inspection_counter:04d}"
                ),
                "machine_id": machine_id,
                "production_run_reference": production_ref,
                "inspection_date": target_date.isoformat(),
                "defect_type_id": defect["defect_type_id"] if defect else None,
                "units_inspected": units_inspected,
                "units_rejected": rejected,
                "inspector_id": (
                    random.choice(inspector_pool)
                    if random.random() > 0.20
                    else None
                ),
                "data_entry_method": random.choices(
                    ["Manual", "ERP Export"],
                    weights=[0.75, 0.25],
                )[0],
                "entered_by": f"EMP-{random.randint(100, 999):04d}",
                "entered_at": format_iso_timestamp(entered_at),
            }
        )
        inspection_counter += 1

    return rows


def generate_malformed_production_sample(target_date=None):
    if target_date is None:
        target_date = datetime.now().date()

    machine_id = random.choice(MACHINE_IDS)
    shift = random.choice(SHIFTS)
    product_id = random.choice(PRODUCT_IDS)

    start_time = datetime.combine(target_date, datetime.min.time()) + timedelta(
        hours=8, minutes=0
    )
    end_time = start_time + timedelta(hours=2)

    return [
        {
            "log_reference_number": f"LOG-MALFORMED-{target_date.strftime('%Y%m%d')}",
            "machine_id": machine_id,
            "shift_id": shift["shift_id"],
            "product_id": product_id,
            "run_date": target_date.isoformat(),
            "run_sequence_number": 1,
            "run_start_time": format_iso_timestamp(start_time),
            "run_end_time": format_iso_timestamp(end_time),
            "planned_units": 500,
            "produced_units": "unknown",  # intentional string violation
            "good_units": 450,
            "operator_id": f"EMP-{random.randint(100, 999):04d}",
            "notes": "Malformed record for testing",
            "data_entry_method": "Manual",
            "entered_by": f"EMP-{random.randint(100, 999):04d}",
            "entered_at": format_iso_timestamp(end_time + timedelta(minutes=30)),
        }
    ]


# ===========================================================================
# SECTION 10 -- CSV WRITER & MAIN
# ===========================================================================


def write_csv(filename, rows, fieldnames):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for FPLIP")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD)", default=None)
    parser.add_argument(
        "--rows", type=int, default=50, help="Number of rows per transactional source"
    )
    parser.add_argument(
        "--output-dir", default="data/incoming", help="Output directory"
    )
    args = parser.parse_args()

    target_date = (
        datetime.strptime(args.date, "%Y-%m-%d").date()
        if args.date
        else datetime.now().date()
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic data for {target_date.isoformat()}")
    print("=" * 50)

    # Master data generated first to ensure FK alignment
    print("\n[>] Generating master data...")

    machine_rows = generate_machine_master(10)
    write_csv(output_dir / "machines.csv", machine_rows, get_machine_fields())
    print(f"   machines.csv: {len(machine_rows)} rows")

    product_rows = generate_product_master(20)
    write_csv(output_dir / "products.csv", product_rows, get_product_fields())
    print(f"   products.csv: {len(product_rows)} rows")

    shift_rows = generate_shift_master()
    write_csv(output_dir / "shifts.csv", shift_rows, get_shift_fields())
    print(f"   shifts.csv: {len(shift_rows)} rows")

    reason_rows = generate_downtime_reason_master()
    write_csv(
        output_dir / "downtime_reasons.csv", reason_rows, get_downtime_reason_fields()
    )
    print(f"   downtime_reasons.csv: {len(reason_rows)} rows")

    defect_rows = generate_defect_type_master()
    write_csv(output_dir / "defect_types.csv", defect_rows, get_defect_type_fields())
    print(f"   defect_types.csv: {len(defect_rows)} rows")

    # Transactional data
    print("\n[>] Generating transactional data...")

    valid_product_ids = [r["product_id"] for r in product_rows]
    production_fields = [
        "log_reference_number",
        "machine_id",
        "shift_id",
        "product_id",
        "run_date",
        "run_sequence_number",
        "run_start_time",
        "run_end_time",
        "planned_units",
        "produced_units",
        "good_units",
        "operator_id",
        "notes",
        "data_entry_method",
        "entered_by",
        "entered_at",
    ]

    prod_rows = generate_production_sample(target_date, args.rows, valid_product_ids, machine_rows=machine_rows)
    write_csv(
        output_dir / f"production_{target_date.strftime('%Y%m%d')}.csv",
        prod_rows,
        production_fields,
    )
    print(f"   production_{target_date.strftime('%Y%m%d')}.csv: {len(prod_rows)} rows")

    downtime_fields = [
        "event_id",
        "machine_id",
        "shift_id",
        "event_date",
        "reason_id",
        "reason_free_text",
        "start_time",
        "end_time",
        "duration_sec",
        "data_entry_method",
        "entered_by",
        "entered_at",
    ]

    downtime_rows = generate_downtime_sample(target_date, max(10, args.rows // 2))
    write_csv(
        output_dir / f"downtime_{target_date.strftime('%Y%m%d')}.csv",
        downtime_rows,
        downtime_fields,
    )
    print(
        f"   downtime_{target_date.strftime('%Y%m%d')}.csv: {len(downtime_rows)} rows"
    )

    qc_fields = [
        "inspection_id",
        "machine_id",
        "production_run_reference",
        "inspection_date",
        "defect_type_id",
        "units_inspected",
        "units_rejected",
        "inspector_id",
        "data_entry_method",
        "entered_by",
        "entered_at",
    ]

    qc_rows = generate_qc_sample(target_date, max(10, args.rows // 2), prod_rows=prod_rows)
    write_csv(
        output_dir / f"qc_{target_date.strftime('%Y%m%d')}.csv", qc_rows, qc_fields
    )
    print(f"   qc_{target_date.strftime('%Y%m%d')}.csv: {len(qc_rows)} rows")

    malformed_rows = generate_malformed_production_sample(target_date)
    write_csv(
        output_dir / f"production_malformed_{target_date.strftime('%Y%m%d')}.csv",
        malformed_rows,
        production_fields,
    )
    print(
        "   production_malformed_"
        f"{target_date.strftime('%Y%m%d')}.csv: 1 row (produced_units = 'unknown')"
    )

    print("\n" + "=" * 50)
    print("[OK] All data generated successfully!")
    print(f"   Output directory: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
