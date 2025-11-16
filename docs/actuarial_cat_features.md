# Advanced Actuarial and CAT/Accumulation Features

## Overview
This document describes the advanced actuarial and catastrophe (CAT) modeling features implemented in the risk simulation tool. These enhancements enable sophisticated insurance and reinsurance risk analysis, including layer modeling, geographic exposure tracking, and catastrophic event analysis.

## Actuarial Features

### 1. Burning Cost Rate
The **burning cost** represents the average annual loss as a percentage of the total portfolio value. This is a fundamental actuarial metric used in insurance pricing.

**Calculation:**
```
burning_cost = mean_loss / portfolio_value
```

**Use Case:** Pricing insurance premiums, evaluating historical loss patterns, and setting reserves.

### 2. Insurance Layers
Insurance layers model the structure of insurance coverage with deductibles, limits, and participation (coinsurance) rates.

**Components:**
- **Deductible (Attachment Point):** The loss threshold before coverage begins
- **Limit:** Maximum coverage provided by the layer
- **Participation Rate:** The percentage of excess losses covered (for coinsurance)
- **Premium Rate:** Optional premium as a fraction of portfolio value

**Example:**
```json
{
  "layers": [
    {
      "deductible": 100000,
      "limit": 2000000,
      "participation": 0.8,
      "premium_rate": 0.015
    }
  ]
}
```

This represents coverage where:
- First $100,000 of losses are retained
- Next $2,000,000 of losses are 80% covered
- Premium is 1.5% of portfolio value

### 3. Loss Ratio
The **loss ratio** measures the efficiency of insurance coverage by comparing actual losses to premiums collected.

**Calculation:**
```
loss_ratio = total_layer_losses / total_premiums
```

**Interpretation:**
- Loss ratio < 1.0: Profitable coverage
- Loss ratio > 1.0: Unprofitable coverage
- Typical target: 0.60-0.70 for most insurance lines

### 4. Net Retained Loss
After applying insurance layers, the **net retained loss** represents the portion of losses still borne by the insured entity.

**Use Case:** Evaluating the effectiveness of insurance programs and optimizing layer structures.

## CAT/Accumulation Features

### 1. CAT Event Identification
Risk factors can be marked as catastrophic events using the `is_cat_event` flag. CAT events are characterized by:
- Low frequency (rare occurrence)
- High severity (large losses)
- Potential for aggregation across multiple exposures

**Example:**
```json
{
  "name": "Hurricane (CAT)",
  "frequency": 0.05,
  "severity_mean": 3500000,
  "severity_std": 1800000,
  "distribution": "pareto",
  "is_cat_event": true
}
```

### 2. Geographic Exposure Tracking
The `geographic_zone` attribute enables spatial correlation analysis and accumulation tracking.

**Use Case:** 
- Identifying concentration risk in specific regions
- Managing geographic diversification
- Assessing exposure to regional catastrophes

**Output:**
```json
{
  "geographic_exposure": {
    "Gulf Coast": 175000,
    "California": 250000,
    "Florida": 195000
  }
}
```

### 3. OEP Curve (Occurrence Exceedance Probability)
The OEP curve shows the loss amount that has a specific probability of being exceeded by the largest single event in a year.

**Return Periods Calculated:** 10, 25, 50, 100, 250, 500 years

**Interpretation:**
- OEP at 100 years: There's a 1% annual probability of the single worst event exceeding this loss amount
- Used for capacity planning and catastrophe bond pricing

**Example:**
```json
{
  "oep_curve": [
    {"level": 10, "value": 1200000},
    {"level": 100, "value": 5500000},
    {"level": 500, "value": 12000000}
  ]
}
```

### 4. AEP Curve (Aggregate Exceedance Probability)
The AEP curve shows the total annual loss amount that has a specific probability of being exceeded when considering all events in a year.

**Key Difference from OEP:** AEP aggregates all events in a year, while OEP considers only the largest event.

**Use Case:** Total loss budgeting, setting aggregate deductibles, and evaluating portfolio-level exposure.

### 5. PML (Probable Maximum Loss)
PML represents the loss amount expected at specific return periods, commonly used in insurance and reinsurance.

**Standard Return Periods:** 100, 250, 500 years

**Example:**
```json
{
  "pml_values": {
    "pml_100y": 5200000,
    "pml_250y": 8900000,
    "pml_500y": 12500000
  }
}
```

**Use Case:**
- Capital requirement calculations (e.g., Solvency II)
- Reinsurance treaty structuring
- Risk appetite setting

### 6. CAT Event Count
Tracks the number of catastrophic events occurring across all simulation trials.

**Use Case:** Validating frequency assumptions and understanding event clustering.

## API Usage Examples

### Example 1: Basic Actuarial Analysis
```json
{
  "trials": 10000,
  "seed": 42,
  "meta": {
    "portfolio_value": 50000000,
    "horizon_months": 12,
    "label": "Property Portfolio"
  },
  "factors": [
    {
      "name": "Fire Loss",
      "frequency": 0.3,
      "severity_mean": 500000,
      "severity_std": 250000,
      "distribution": "lognormal"
    }
  ],
  "layers": [
    {
      "deductible": 250000,
      "limit": 5000000,
      "participation": 1.0,
      "premium_rate": 0.02
    }
  ]
}
```

**Key Outputs:**
- `burning_cost`: Annual loss rate
- `loss_ratio`: Profitability of coverage
- `net_retained_loss`: Expected retained amount
- `layer_losses.layer_0`: Expected insurance payout

### Example 2: CAT Exposure Analysis
```json
{
  "trials": 50000,
  "seed": 123,
  "meta": {
    "portfolio_value": 100000000,
    "horizon_months": 12,
    "label": "Hurricane Exposure"
  },
  "factors": [
    {
      "name": "Florida Hurricane",
      "frequency": 0.08,
      "severity_mean": 10000000,
      "severity_std": 5000000,
      "distribution": "pareto",
      "is_cat_event": true,
      "geographic_zone": "Florida"
    },
    {
      "name": "Gulf Coast Hurricane",
      "frequency": 0.06,
      "severity_mean": 8000000,
      "severity_std": 4000000,
      "distribution": "pareto",
      "is_cat_event": true,
      "geographic_zone": "Gulf Coast"
    }
  ]
}
```

**Key Outputs:**
- `oep_curve`: Single-event exceedance probabilities
- `aep_curve`: Aggregate annual exceedance probabilities
- `pml_values`: Probable maximum losses
- `geographic_exposure`: Exposure by region

### Example 3: Combined Actuarial and CAT Analysis
```json
{
  "trials": 20000,
  "seed": 456,
  "meta": {
    "portfolio_value": 75000000,
    "horizon_months": 12,
    "label": "Comprehensive Risk Model"
  },
  "factors": [
    {
      "name": "Operational Risk",
      "frequency": 2.0,
      "severity_mean": 100000,
      "severity_std": 50000,
      "distribution": "lognormal",
      "geographic_zone": "Global"
    },
    {
      "name": "Earthquake",
      "frequency": 0.02,
      "severity_mean": 15000000,
      "severity_std": 8000000,
      "distribution": "pareto",
      "is_cat_event": true,
      "geographic_zone": "California"
    }
  ],
  "layers": [
    {
      "deductible": 500000,
      "limit": 10000000,
      "participation": 0.75,
      "premium_rate": 0.025
    }
  ]
}
```

**Key Outputs:**
- All actuarial metrics (burning cost, loss ratio, layer losses)
- All CAT metrics (OEP, AEP, PML, event counts)
- Geographic exposure breakdown

## Mathematical Formulations

### Layer Loss Calculation
For each trial `t` with gross loss `L_t`:

1. **Excess over deductible:**
   ```
   E_t = max(L_t - D, 0)
   ```
   where D = deductible

2. **Apply limit:**
   ```
   C_t = min(E_t, Limit)
   ```

3. **Apply participation:**
   ```
   Layer_Loss_t = C_t × p
   ```
   where p = participation rate

4. **Net retained:**
   ```
   Net_t = L_t - Layer_Loss_t
   ```

### OEP/AEP Calculation
For return period `RP`:
- Exceedance probability: `EP = 1 / RP`
- Percentile level: `q = 1 - EP`
- OEP/AEP value: `quantile(losses, q)`

### Return Period Interpretation
| Return Period | Annual Exceedance Probability | Percentile |
|---------------|-------------------------------|------------|
| 10 years      | 10%                          | 90th       |
| 50 years      | 2%                           | 98th       |
| 100 years     | 1%                           | 99th       |
| 250 years     | 0.4%                         | 99.6th     |
| 500 years     | 0.2%                         | 99.8th     |

## Best Practices

### For Actuarial Analysis
1. **Layer Optimization:** Test multiple layer structures to find optimal deductible/limit combinations
2. **Premium Adequacy:** Ensure loss ratios are sustainable (typically < 0.80)
3. **Retention Levels:** Set deductibles based on risk appetite and capital constraints

### For CAT Modeling
1. **Sufficient Trials:** Use at least 10,000 trials for CAT events; 50,000+ for stable tail estimates
2. **Distribution Selection:** Use Pareto distribution for CAT events to capture heavy tails
3. **Return Period Selection:** Focus on 100-year and 250-year return periods for regulatory compliance
4. **Geographic Diversification:** Monitor concentration in single zones

### For Combined Analysis
1. **Separate CAT and Non-CAT:** Model separately to understand different risk drivers
2. **Stress Testing:** Run scenarios with multiple CAT events in a single year
3. **Correlation Assumptions:** Consider adding spatial correlation for nearby geographic zones
4. **Documentation:** Always save seed values for reproducibility

## Limitations and Future Enhancements

### Current Limitations
- Geographic zones are independent (no spatial correlation)
- OEP/AEP use same underlying loss distribution (simplified)
- Layers are applied globally, not per-zone
- No secondary uncertainty (parameter uncertainty)

### Planned Enhancements
- Spatial correlation matrices for geographic zones
- Multiple layer structures (primary + excess layers)
- Reinsurance treaty modeling (quota share, surplus)
- Tail dependency modeling
- Climate change trend adjustments
- Historical event validation

## References
- Actuarial Standards Board. "Modeling" (ASOP No. 38)
- Society of Actuaries. "Enterprise Risk Management"
- AIR Worldwide. "Probable Maximum Loss (PML)"
- RMS. "Exceedance Probability Curves in Catastrophe Modeling"
