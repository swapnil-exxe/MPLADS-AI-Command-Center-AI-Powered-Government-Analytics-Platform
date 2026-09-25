from typing import List, Tuple
from scraper.models import NormalizedWorkModel, ValidationResultModel

class DataValidator:
    """
    Quality control and integrity validator for incoming works.
    Ensures validation passes before database mutation occurs.
    """

    @classmethod
    def validate_batch(cls, works: List[NormalizedWorkModel]) -> Tuple[ValidationResultModel, List[NormalizedWorkModel]]:
        errors = []
        warnings = []
        valid_works = []
        invalid_count = 0

        if not works:
            return ValidationResultModel(
                is_valid=True,
                total_records=0,
                valid_records=0,
                invalid_records=0,
                errors=["Empty payload"],
                warnings=[]
            ), []

        for idx, w in enumerate(works):
            record_errors = []

            # 1. Required Identifiers
            if not w.work_id or not w.work_id.strip():
                record_errors.append(f"Row {idx}: Missing work_id")

            if not w.state or not w.state.strip():
                record_errors.append(f"Row {idx} ({w.work_id}): Missing state")

            if not w.district or not w.district.strip():
                record_errors.append(f"Row {idx} ({w.work_id}): Missing district")

            # 2. Financial Amount Checks
            if w.sanction_amount is not None and w.sanction_amount < 0:
                record_errors.append(f"Row {idx} ({w.work_id}): Negative sanction amount {w.sanction_amount}")

            if w.amount_disbursed is not None and w.amount_disbursed < 0:
                record_errors.append(f"Row {idx} ({w.work_id}): Negative disbursed amount {w.amount_disbursed}")

            if (w.sanction_amount is not None and w.amount_disbursed is not None and 
                w.amount_disbursed > w.sanction_amount * 5.0 and w.sanction_amount > 1000):
                warnings.append(f"Row {idx} ({w.work_id}): Disbursed amount ({w.amount_disbursed}) is 5x sanction amount ({w.sanction_amount})")

            # 3. Date Sequence Check
            if w.recommended_date and w.sanction_date:
                if w.sanction_date < w.recommended_date:
                    warnings.append(f"Row {idx} ({w.work_id}): Sanction date ({w.sanction_date}) precedes recommendation date ({w.recommended_date})")

            if record_errors:
                errors.extend(record_errors)
                invalid_count += 1
            else:
                valid_works.append(w)

        is_valid = invalid_count == 0 or (len(valid_works) / len(works) >= 0.90)

        result_model = ValidationResultModel(
            is_valid=is_valid,
            total_records=len(works),
            valid_records=len(valid_works),
            invalid_records=invalid_count,
            errors=errors[:50],  # Truncate for report summary
            warnings=warnings[:50]
        )

        return result_model, valid_works
