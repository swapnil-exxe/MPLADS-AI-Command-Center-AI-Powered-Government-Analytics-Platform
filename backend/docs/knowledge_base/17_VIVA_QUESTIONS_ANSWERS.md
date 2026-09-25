# 17. Viva Questions & Expert Answers

## Technical Viva Questions & Detailed Answers

### Q1: Why did you split anomaly detection into 4 separate models instead of calculating a single composite risk score?
- **Short Answer**: To preserve signal fidelity. Cost overruns, duplicate billing, dormant funds, and statutory delays are fundamentally different risk dimensions.
- **Detailed Answer**: A composite score averages distinct signals. An urgently completed hospital could have zero delay and valid vouchers but an inflated cost estimate. Averaging these scores would mask the cost anomaly. Keeping models independent gives vigilance officers precise, actionable diagnostic reasons for each domain.
- **If Examiner Asks "Why?"**: Composite scores create false negatives by diluting extreme single-dimension anomalies.

---

### Q2: How does Model 1 guarantee zero data leakage?
- **Short Answer**: It evaluates works strictly using features available at sanction time.
- **Detailed Answer**: Model 1 uses only `sanction_amount`, `work_type`, and `state`. It strictly excludes post-sanction features like completion dates, voucher counts, or disbursement amounts.

---

### Q3: How do you prevent Username Enumeration and Timing Attacks on the Login endpoint?
- **Short Answer**: By executing a constant-time dummy bcrypt hash calculation when an email is not found.
- **Detailed Answer**: Standard backends return immediately if an email doesn't exist (~2ms), but execute bcrypt (~90ms) if the email exists. Attackers measure this time difference to harvest valid emails. We execute `DUMMY_BCRYPT_HASH` when an email is missing, forcing every request to take ~90ms regardless of validity.

---

### Q4: Why is District Officer scoping based on `(state, district)` tuples rather than district names alone?
- **Short Answer**: Because district names in India are not unique across states.
- **Detailed Answer**: Exactly 75 district names exist in multiple states (e.g. Bilaspur in Chhattisgarh and Himachal Pradesh). Scoping by district name alone would leak data across state boundaries. We enforce composite tuple scoping: `(assigned_state, assigned_district)`.

