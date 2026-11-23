"""Illustrative, sourced section properties used by Beam Designer."""

MEMBERS = {
    "W12x26 (A992 steel)": {
        "material": "Steel",
        "E_ksi": 29000.0,
        "I_in4": 204.0,
        "S_in3": 33.4,
        "allowable_bending_ksi": 33.0,
        "basis": "Illustrative historical 0.66 Fy value; fully braced compact section assumption.",
        "source": "AISC/A992 and W12x26 references in 01_data/illustrative-properties.md",
    },
    "Southern Pine No. 2 2x8": {
        "material": "Lumber",
        "E_ksi": 1400.0,
        "I_in4": 47.63,
        "S_in3": 13.14,
        "allowable_bending_ksi": 1.065,
        "basis": "Normal duration; values and adjustment assumptions per AWC table.",
        "source": "AWC 2024 and dimension references in 01_data/illustrative-properties.md",
    },
}
