"""
Module D: Monte Carlo Scenario Engine
Section 7 Item 3: Distribution Honesty & Counterfactual Sampling

DISCLOSURE & METHODOLOGY ASSUMPTIONS:
The continuous outcome distributions across severity states (e.g. Normal distributions
for High/Medium/Low assembly drop) and the downstream spot premium multipliers
(Uniform[1.3, 2.8]) are calibrated engineering/economic assumptions, NOT empirical
econometric fits to historical loss data. They are designed for counterfactual stress
testing, supply chain resilience modeling, and scenario analysis. Downstream consumers
and reporting interfaces must disclose these as calibrated assumptions rather than
misrepresenting them as fitted distributions.
"""

import time
import logging
from typing import Dict, Any, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class MonteCarloResult(dict):
    """
    Result container for Monte Carlo simulation.
    Inherits from dict so that `result['distribution_source']`, `result['samples']`, etc.
    work directly as a return dict, while also supporting numpy array operations
    and conversions (len, iter, math, indexing) for seamless downstream compatibility.
    """
    def __init__(
        self,
        samples: np.ndarray,
        distribution_source: str = "calibrated_estimate",
        random_seed: Optional[int] = 42,
        **kwargs
    ):
        super().__init__()
        self["samples"] = samples
        self["distribution_source"] = distribution_source
        self["random_seed"] = random_seed
        self["mean_drop"] = float(np.mean(samples))
        self["median_drop"] = float(np.median(samples))
        self["p95_drop"] = float(np.percentile(samples, 95))
        self["p99_drop"] = float(np.percentile(samples, 99))
        self["n_samples"] = len(samples)
        for k, v in kwargs.items():
            self[k] = v

    def __array__(self, dtype=None):
        return np.asarray(self["samples"], dtype=dtype)

    def __len__(self):
        return len(self["samples"])

    def __iter__(self):
        return iter(self["samples"])

    def __getitem__(self, item):
        # Support dict key access first
        if isinstance(item, str):
            return super().__getitem__(item)
        # Fall back to indexing the underlying numpy samples array
        return self["samples"][item]

    def __truediv__(self, other):
        return self["samples"] / other

    def __rtruediv__(self, other):
        return other / self["samples"]

    def __mul__(self, other):
        return self["samples"] * other

    def __rmul__(self, other):
        return other * self["samples"]

    def __add__(self, other):
        return self["samples"] + other

    def __radd__(self, other):
        return other + self["samples"]

    def __sub__(self, other):
        return self["samples"] - other

    def __rsub__(self, other):
        return other - self["samples"]


def run_monte_carlo(
    probabilities: dict,
    n_samples: int = 10000,
    random_seed: Optional[int] = 42,
    distribution_source: str = "calibrated_estimate"
) -> MonteCarloResult:
    """
    Runs a 10,000-draw Monte Carlo scenario simulation based on causal posterior probabilities.

    HONESTY & CALIBRATION DISCLOSURE (Section 7, Item 3):
    -----------------------------------------------------
    The continuous state distributions (Normal distributions for High, Medium, Low states)
    and downstream spot premium multipliers (Uniform[1.3, 2.8]) are CALIBRATED ASSUMPTIONS,
    NOT fitted empirical distributions. They represent engineering and domain-calibrated
    stress-testing parameters for automotive semiconductor supply chains. They must never
    be misrepresented downstream as econometric or historical empirical fits.

    Args:
        probabilities: Probability distribution dict from Module C (simulate_causal_impact),
                       containing state marginals and '_risk_meta'.
        n_samples: Number of counterfactual scenario draws (default 10,000).
        random_seed: Integer seed for reproducible pseudo-random draws across runs
                     (default 42, pass None for unseeded stochastic runs).
        distribution_source: Declaration of distributional origin:
                             'calibrated_estimate' (current state, default assumption) or
                             'empirical_fit' (reserved for future econometric calibration).

    Returns:
        A return dict (MonteCarloResult) containing:
        - "distribution_source": "calibrated_estimate" (or passed value)
        - "samples": np.ndarray of simulated production drop percentages
        - "random_seed": the seed used for reproducibility
        - "mean_drop": mean production drop percentage
        - "p95_drop": 95th percentile production drop percentage
        - "p99_drop": 99th percentile production drop percentage
        - "n_samples": number of simulation iterations
        (Also supports direct array operations for full backward compatibility).
    """
    logger.info(f"Running Monte Carlo with {n_samples} samples (seed={random_seed}, source={distribution_source})...")

    # Validate / enforce distribution_source
    if distribution_source not in ("calibrated_estimate", "empirical_fit"):
        logger.warning(
            f"Unrecognized distribution_source '{distribution_source}'. "
            "Defaulting to 'calibrated_estimate'."
        )
        distribution_source = "calibrated_estimate"

    # Reproducibility via fixed random seed
    if random_seed is not None:
        rng = np.random.RandomState(random_seed)
        np.random.seed(random_seed)
    else:
        rng = np.random.RandomState()

    # Define discrete severity states
    states = ["High (>15%)", "Medium (5-15%)", "Low (<5%)", "None"]

    # Extract probabilities ensuring they sum to 1
    probs_array = [
        probabilities.get(states[0], 0.0),
        probabilities.get(states[1], 0.0),
        probabilities.get(states[2], 0.0),
        probabilities.get(states[3], 0.0)
    ]
    total_prob = sum(probs_array)
    if total_prob > 0:
        probs_array = np.array(probs_array) / total_prob
    else:
        probs_array = np.array([0.25, 0.25, 0.25, 0.25])

    # 1. Sample the categorical state for each run
    state_choices = rng.choice(states, size=n_samples, p=probs_array)

    # 2. Draw from the appropriate continuous distribution for each state
    samples = np.zeros(n_samples)

    # High: dynamic mean calibrated to structural shock intensity (20% to 36%)
    risk_meta = probabilities.get("_risk_meta", {})
    r_score = risk_meta.get("risk_score", 0.5) if isinstance(risk_meta, dict) else 0.5
    high_loc = 20.0 + 16.0 * max(0.0, min(1.0, (r_score - 0.50) / 0.40))

    high_mask = (state_choices == states[0])
    samples[high_mask] = rng.normal(loc=high_loc, scale=3.5, size=np.sum(high_mask))

    # Medium: mean 10, std 2
    med_mask = (state_choices == states[1])
    samples[med_mask] = rng.normal(loc=10.0, scale=2.0, size=np.sum(med_mask))

    # Low: mean 2, std 1
    low_mask = (state_choices == states[2])
    samples[low_mask] = rng.normal(loc=2.0, scale=1.0, size=np.sum(low_mask))

    # None: exactly 0
    none_mask = (state_choices == states[3])
    samples[none_mask] = 0.0

    # Clip just in case tails cross 0
    samples = np.clip(samples, 0, 100)

    logger.info(f"Generated {len(samples)} samples. Mean drop: {np.mean(samples):.2f}%")
    return MonteCarloResult(
        samples=samples,
        distribution_source=distribution_source,
        random_seed=random_seed,
    )
