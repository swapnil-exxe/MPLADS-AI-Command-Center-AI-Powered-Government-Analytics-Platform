# 07. Feature Engineering Registry

## Feature Engineering Pipeline (`feature_engineering/`)

The feature engineering registry converts raw portal records into clean analytical matrices:

### Core Feature Transformations

1. **Log Transformations**: `sanction_amount_log`, `log_disbursed_amount`, `days_to_first_disbursement_log` to eliminate monetary skewness.
2. **IQR Deviations**: Cost ratio vs peer group median and IQR deviation metrics.
3. **Herfindahl-Hirschman Index (HHI)**:
   $$\text{HHI} = \sum_{i=1}^{n} \left(\frac{\text{voucher\_amount}_i}{\text{total\_disbursed}}\right)^2$$
   Measures voucher disbursement concentration (1.0 = lump-sum single release, <0.2 = gradual phased tranches).
4. **Temporal Lag Vectors**: Elapsed days between recommendation, sanction, first voucher, last voucher, and completion.

