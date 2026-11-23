"""Elastic beam calculations, independent of the user interface.

Internal units: kip, inch, ksi. Loads are downward-positive magnitudes; positive
moment is sagging. Euler-Bernoulli integration uses a uniform x grid.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class UniformLoad:
    intensity_kip_ft: float
    start_ft: float
    end_ft: float


def analyze(span_ft, support, loads, member, safety_factor=1.0, points=1201):
    """Return equilibrium, sampled diagrams, extrema, and separate checks."""
    L = float(span_ft) * 12.0
    if not np.isfinite(L) or L <= 0:
        raise ValueError("Span must be a finite number greater than zero.")
    if support not in ("Simply supported", "Cantilever"):
        raise ValueError("Unsupported support condition.")
    if not np.isfinite(safety_factor) or safety_factor < 1:
        raise ValueError("Safety factor must be at least 1.0.")

    wloads = []
    for load in loads:
        w, a, b = map(float, (load.intensity_kip_ft, load.start_ft, load.end_ft))
        if not all(map(np.isfinite, (w, a, b))) or w < 0 or a < 0 or b <= a or b > span_ft:
            raise ValueError("Each load needs finite values, 0 ≤ start < end ≤ span, and nonnegative intensity.")
        wloads.append((w / 12.0, a * 12.0, b * 12.0))

    E, I, S = member["E_ksi"], member["I_in4"], member["S_in3"]
    x = np.linspace(0, L, points)
    total = sum(w * (b-a) for w, a, b in wloads)
    centroid_moment = sum(w * (b-a) * (a+b)/2 for w, a, b in wloads)
    if support == "Simply supported":
        right = centroid_moment / L
        left = total - right
        V = left - sum((w * np.clip(x-a, 0, b-a) for w, a, b in wloads), np.zeros_like(x))
        M = left*x - sum((w * np.where(x <= a, 0, np.where(x < b, (x-a)**2/2, (b-a)*(x-(a+b)/2))) for w, a, b in wloads), np.zeros_like(x))
        curvature = M / (E*I)
        dx = x[1]-x[0]
        slope0 = -np.trapezoid((L-x)*curvature, x) / L
        slope = slope0 + np.concatenate(([0.], np.cumsum((curvature[:-1]+curvature[1:])*dx/2)))
        deflection = np.concatenate(([0.], np.cumsum((slope[:-1]+slope[1:])*dx/2)))
        left_moment = 0.0
    else:
        left, right = total, 0.0
        left_moment = -centroid_moment
        V = -sum((w * np.clip(b-np.maximum(x, a), 0, b-a) for w, a, b in wloads), np.zeros_like(x))
        M = -sum((w * (np.clip(b-x, 0, None)**2 - np.clip(a-x, 0, None)**2)/2 for w, a, b in wloads), np.zeros_like(x))
        # Integrate from fixed end: y(0)=slope(0)=0.
        curvature = M / (E*I)
        dx = x[1]-x[0]
        slope = np.concatenate(([0.], np.cumsum((curvature[:-1]+curvature[1:])*dx/2)))
        deflection = np.concatenate(([0.], np.cumsum((slope[:-1]+slope[1:])*dx/2)))

    im = int(np.argmax(np.abs(M)))
    idf = int(np.argmax(np.abs(deflection)))
    max_moment_kip_ft = abs(M[im])/12
    stress = max_moment_kip_ft*12/S
    stress_limit = member["allowable_bending_ksi"] / safety_factor
    limit_in = L/360
    return {"x_ft": x/12, "shear_kip": V, "moment_kip_ft": M/12,
            "deflection_in": deflection, "reaction_left_kip": left,
            "reaction_right_kip": right, "fixed_moment_kip_ft": left_moment/12,
            "max_moment_kip_ft": max_moment_kip_ft, "moment_at_ft": x[im]/12,
            "max_deflection_in": abs(deflection[idf]), "deflection_at_ft": x[idf]/12,
            "bending_stress_ksi": stress, "bending_limit_ksi": stress_limit,
            "bending_pass": stress <= stress_limit, "deflection_limit_in": limit_in,
            "deflection_pass": abs(deflection[idf]) <= limit_in}
