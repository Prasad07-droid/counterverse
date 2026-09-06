"""
Module D: Monte Carlo Scenario Engine (Dummy Implementation for Phase 1)

This module generates a distribution of production drop outcomes based on the 
probabilities from the causal model.
"""

import time
import numpy as np
import logging

logger = logging.getLogger(__name__)

def run_monte_carlo(probabilities: dict, n_samples: int = 10000) -> np.ndarray:
    """
    Runs a dummy Monte Carlo simulation based on causal probabilities.
    
    Args:
        probabilities: Probability distribution from Module C.
        n_samples: Number of samples to generate.
        
    Returns:
        A numpy array of simulated production drop percentages.
    """
    logger.info(f"Running Monte Carlo with {n_samples} samples...")
    
    # Simulate processing time
    time.sleep(1.0)
    
    # Define the discrete severity states
    states = ["High (>15%)", "Medium (5-15%)", "Low (<5%)", "None"]
    
    # Extract probabilities ensuring they sum to 1
    probs_array = [
        probabilities.get(states[0], 0.0),
        probabilities.get(states[1], 0.0),
        probabilities.get(states[2], 0.0),
        probabilities.get(states[3], 0.0)
    ]
    probs_array = np.array(probs_array) / np.sum(probs_array)
    
    # 1. Sample the categorical state for each of the 10,000 runs
    state_choices = np.random.choice(states, size=n_samples, p=probs_array)
    
    # 2. Draw from the appropriate continuous distribution for each state
    samples = np.zeros(n_samples)
    
    # High: dynamic mean calibrated to structural shock intensity (20% to 36%)
    risk_meta = probabilities.get("_risk_meta", {})
    r_score = risk_meta.get("risk_score", 0.5) if isinstance(risk_meta, dict) else 0.5
    high_loc = 20.0 + 16.0 * max(0.0, min(1.0, (r_score - 0.50) / 0.40))
    
    high_mask = state_choices == states[0]
    samples[high_mask] = np.random.normal(loc=high_loc, scale=3.5, size=np.sum(high_mask))
    
    # Medium: mean 10, std 2
    med_mask = state_choices == states[1]
    samples[med_mask] = np.random.normal(loc=10.0, scale=2.0, size=np.sum(med_mask))
    
    # Low: mean 2, std 1
    low_mask = state_choices == states[2]
    samples[low_mask] = np.random.normal(loc=2.0, scale=1.0, size=np.sum(low_mask))
    
    # None: exactly 0
    none_mask = state_choices == states[3]
    samples[none_mask] = 0.0
    
    # Clip just in case tails cross 0
    samples = np.clip(samples, 0, 100)
    
    logger.info(f"Generated {len(samples)} samples. Mean drop: {np.mean(samples):.2f}%")
    return samples
