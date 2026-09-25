# 08. Statutory SLA Rule Engine

## Statutory Delay SLA Rule Engine (`rule_engines/delay/`)

Statutory compliance in government schemes is a legal mandate, requiring a deterministic Rule Engine rather than a probabilistic ML model.

### SLA Thresholds & Severity Mapping

- **Sanction SLA (Para 3.12 - 75 Days)**:
  - $\le 75\text{ days}$: `NONE` (Compliant)
  - $76 - 150\text{ days}$: `LOW`
  - $151 - 225\text{ days}$: `MEDIUM`
  - $> 225\text{ days}$: `HIGH` (>3x legal limit)

- **Execution SLA (365 Days)**:
  - $\le 365\text{ days}$: `NONE` (Compliant)
  - $366 - 548\text{ days}$: `LOW`
  - $549 - 730\text{ days}$: `MEDIUM`
  - $> 730\text{ days}$: `HIGH` (>2 years elapsed)

- **Open Work Aging**:
  - Evaluates active elapsed days from sanction date to fixed reference date `2026-09-05`.

