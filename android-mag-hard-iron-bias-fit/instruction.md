I work on the Android factory line calibrating magnetometers. Every phone has small magnets inside from speakers and screws that add a constant offset to the magnetometer. We call it hard iron bias. During factory test we rotate the phone in a figure eight and log raw magnetic field values. If there were no bias those values would sit on a sphere centered at zero with radius equal to earth field strength, about 35 to 60 uT. With bias the sphere is shifted. So each reading is true point on sphere plus bias plus noise.

I need a tool that can estimate the bias vector and the sphere radius from orbit data.

Create a Python module mag_calibration.py in the repository root at /app/mag_calibration.py with this function:

```python
import numpy as np

def estimate_hard_iron_bias(mag_xyz):
    """
    Estimate hard iron bias from magnetometer orbit data.

    Args:
        mag_xyz: np.ndarray of shape (N, 3), dtype float, columns [mx, my, mz] in uT.
                 N >= 50.

    Returns:
        dict with keys:
            "bx": float bias on X axis (uT)
            "by": float bias on Y axis (uT)
            "bz": float bias on Z axis (uT)
            "radius": float estimated geomagnetic field strength (uT), greater than 0
    """
```

Requirements.

1. Function must work for N from 50 to 10000 points.
2. Input may contain Gaussian noise up to std 2.0 uT and may have non uniform angular coverage, partial orbit as low as 40 percent of sphere. It may also contain up to 5 percent outliers that are far from sphere due to motor spikes.
3. Radius R is unknown but expected in range 25 to 65 uT. Bias components are in range negative 80 to 80 uT.
4. You must implement a numerically stable method. In ideal case points satisfy sphere equation where distance from center equals radius. That is (x minus bx) squared plus (y minus by) squared plus (z minus bz) squared equals R squared. With noise this is not exact. You need to find bias and radius that best fit the data. Think about how that sphere equation can be turned into something linear in unknowns. You may use numpy linalg lstsq or similar. Do not use scipy or sklearn, only numpy and standard library.
5. Return floats not numpy scalars to keep JSON serializable.
6. Do not hardcode bias or radius. Must be estimated from data.
7. Be robust. Simple averaging of min and max per axis fails badly when coverage is partial or noise is high. Using the mean of all points as bias also fails because mean of partial orbit is not the sphere center.

Example usage

```python
import numpy as np
from mag_calibration import estimate_hard_iron_bias

data = np.loadtxt("data/sample_orbit.csv", delimiter=",", skiprows=1)
result = estimate_hard_iron_bias(data)
print(result)
```

You can test locally on sample file at data/sample_orbit.csv which has 500 points, bias about 15, negative 20, 8, radius about 45 uT, noise std 0.5 uT. Evaluation harness generates its own hidden datasets and directly calls your function, so do not rely on file paths inside estimate_hard_iron_bias.

Constraints

* Only use numpy and standard library. Do not import scipy, sklearn, torch etc.
* Function must be deterministic.
* Handle degenerate inputs gracefully but you may assume valid data has at least 50 points and not all coplanar. Outliers up to 5 percent may be present.

Evaluation

We test on

* Clean orbit: 300 points, no noise, bias error must be less than 0.3 uT, radius error less than 0.3 uT
* Noisy orbit: 500 points, noise std 1.2 uT, bias error less than 0.9 uT per axis, radius error less than 0.9 uT
* Partial orbit: 200 points covering about 40 to 60 percent of sphere, bias error less than 1.8 uT, radius error less than 1.8 uT
* Strong bias case: bias magnitude greater than 50 uT, bias error less than 1.2 uT
* Outlier case: 400 points with 5 percent far outliers, bias error less than 1.5 uT, radius error less than 1.5 uT, simple least squares without outlier handling fails this by 4 to 8 uT
* Random stress: varying R in 30 to 60 and random bias, 6 cases

All tests import mag_calibration.py and call estimate_hard_iron_bias.

Simple shortcuts are off by a large margin. In our measurements on sample plus 3 heldouts exact grading:

* averaging (max plus min) divided by 2 per axis for bias fails 40 to 70 percent error 15 to 35 uT on partial orbits because min and max do not capture center when coverage is missing
* using mean of points as bias fails 80 to 120 percent error 20 to 50 uT for same reason
* using first point distance as radius fails 50 to 90 percent
* hardcoding sample bias 15, negative 20, 8 fails all hidden tests which use random bias up to 80 uT
* plain least squares without outlier handling fails outlier case by 4 to 8 uT

No fixed shortcut passes within tolerance. Only a genuine precise method that does robust sphere fit, handles partial coverage and outliers, will pass. That is the hard part. Similar to foundry thermal void where thresholding fails and you need conservation, here averaging fails and you need proper geometric fit.

Print bias as JSON if run as script is optional for debugging.
