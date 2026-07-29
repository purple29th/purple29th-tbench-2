# Android Magnetometer Hard-Iron Bias Estimation from Orbit Data

## Background
On Android device manufacturing lines, the 3-axis magnetometer must be calibrated to remove magnetic interference from nearby ferromagnetic components, magnets in speakers, and chassis screws. This interference is called hard-iron bias - a constant additive offset to each axis.

During factory calibration, the device is rotated in a figure-8 motion (orbit) while logging raw magnetometer readings. In the absence of bias, the readings should lie on a sphere centered at the origin, with radius equal to the local geomagnetic field strength (typically 35-60 uT). With hard-iron bias, the sphere is offset: each measurement is `p_raw = p_true_sphere + b + noise`, where `b = [bx, by, bz]` is the unknown bias vector.

Your goal is to estimate `b` and the sphere radius `R` from orbit data.

## Task

Create a Python module `mag_calibration.py` in the repository root (`/app/mag_calibration.py`) with the following function:

```python
import numpy as np

def estimate_hard_iron_bias(mag_xyz: np.ndarray) -> dict:
    """
    Estimate hard-iron bias from magnetometer orbit data.

    Args:
        mag_xyz: np.ndarray of shape (N, 3), dtype float, columns [mx, my, mz] in uT.
                 N >= 50.

    Returns:
        dict with keys:
            "bx": float - bias on X axis (uT)
            "by": float - bias on Y axis (uT)
            "bz": float - bias on Z axis (uT)
            "radius": float - estimated geomagnetic field strength (uT), > 0
    """
```

### Requirements

1. The function must work for N >= 50 and up to 5000 points.
2. Input may contain Gaussian noise up to std=1.5 uT and may have non-uniform angular coverage (partial orbit).
3. Radius `R` is unknown but expected in range [25, 65] uT. Bias components are in range [-80, 80] uT.
4. Implement a numerically stable method. Linear least-squares sphere fitting is sufficient:
   
   Sphere equation: (x-bx)^2 + (y-by)^2 + (z-bz)^2 = R^2
   Expand: x^2+y^2+z^2 -2*bx*x -2*by*y -2*bz*z + (bx^2+by^2+bz^2 - R^2) = 0
   Rearranged: [-2x, -2y, -2z, 1] dot [bx, by, bz, c] = -(x^2+y^2+z^2)
   where c = bx^2+by^2+bz^2 - R^2
   Solve linear system A*u = b via least squares, then R = sqrt(bx^2+by^2+bz^2 - c)

   You may use numpy.linalg.lstsq or similar. Do not use scipy or sklearn - only numpy.

5. Return floats (not numpy scalars) to ensure JSON serializable.
6. Do NOT hardcode bias or radius; must be estimated from data.

### Example usage

```python
import numpy as np
from mag_calibration import estimate_hard_iron_bias

data = np.loadtxt("data/sample_orbit.csv", delimiter=",", skiprows=1)  # shape (N,3)
result = estimate_hard_iron_bias(data)
print(result)
# {"bx": 14.8, "by": -19.7, "bz": 8.2, "radius": 45.1}
```

Save bias to `results/bias.json` when run as script (optional but recommended for debugging):

```bash
python3 mag_calibration.py --input data/sample_orbit.csv --output results/bias.json
```

### Data for local development

A sample orbit file is provided at:

- `data/sample_orbit.csv` - CSV with header `mx,my,mz`, 500 points, bias ~[15,-20,8], radius ~45 uT, noise std 0.5 uT

You can create this file structure locally; the evaluation harness generates its own hidden datasets and directly calls your function, so do not rely on file paths inside `estimate_hard_iron_bias`.

### Constraints

- ONLY use `numpy` (and standard library). Do not import scipy, sklearn, torch, etc.
- Function must be deterministic.
- Handle degenerate inputs gracefully (but you may assume valid data has at least 50 points and not all coplanar).

### Evaluation

Your solution will be tested on:

1. Clean orbit: 300 points, no noise - bias error must be < 0.3 uT, radius error < 0.3 uT
2. Noisy orbit: 500 points, noise std 1.0 uT - bias error < 0.8 uT per axis, radius error < 0.8 uT
3. Partial orbit: 200 points covering ~60% of sphere - bias error < 1.5 uT, radius error < 1.5 uT
4. Strong bias case: bias magnitude > 50 uT - bias error < 1.0 uT
5. Random stress tests with varying R in [30,60] and random bias

All tests import `mag_calibration.py` and call `estimate_hard_iron_bias`.
