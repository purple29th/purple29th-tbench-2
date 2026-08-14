Implement a function that computes the 3D gravitational potential and its gradient at M target points due to N source masses.

The potential at target point `x` due to sources at positions `y_i` with masses `m_i` is:

    Φ(x) = Σ_{i=1}^{N} m_i / |x - y_i|

and the gradient is:

    ∇Φ(x) = -Σ_{i=1}^{N} m_i * (x - y_i) / |x - y_i|³

where `|·|` denotes the Euclidean norm in ℝ³.

## Interface

The function should be called `compute_potential` in `compute_potential.py` with the following signature:

```python
def compute_potential(
    sources: np.ndarray,   # (N, 3) array of source positions
    masses: np.ndarray,    # (N,) array of source masses (positive or negative reals)
    targets: np.ndarray,   # (M, 3) array of target positions
) -> tuple[np.ndarray, np.ndarray]:
    # Returns:
    #   potential: (M,) array of potential values at targets
    #   gradient: (M, 3) array of gradient vectors at targets
```

## Requirements

- **Correctness**: The potential must match the naive O(NM) direct summation to a relative error of at most `1e-4` for each target point (or absolute error `1e-10` when the true value is near zero). The gradient must match to a relative error of at most `1e-2` (or absolute error `1e-8` when the true value is near zero).
- **Performance**: The algorithm must scale as O(N log N) or better — NOT O(N²). This is verified by checking that the normalized runtime t(N)/(N·log(N)) is approximately constant across problem sizes, and that the ratio t(N_max)/t(N_min) over a wide range is consistent with O(N log N).
- **Dependencies**: Only `numpy` and `scipy` (and their sub-modules) are allowed. No other external packages.
- **No precomputation**: The function should be self-contained. Each call is independent — no caching or global state between calls.
- **No targets coinciding with sources**: You may assume that no target point is exactly equal to any source point.
