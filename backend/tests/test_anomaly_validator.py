import pytest
from backend.app.core.anomaly_validator import validate_anomaly_thresholds

def test_validate_anomaly_thresholds_valid():
    scores = [12.5, 45.0, 78.0, 90.0, 30.0]
    result = validate_anomaly_thresholds(scores)

    assert result["valid_scores"] is True
    assert result["mean_score"] == 51.1
    assert result["anomalies_detected"] == 2
    assert result["critical_anomalies"] == 2

def test_validate_anomaly_thresholds_invalid():
    with pytest.raises(ValueError, match="out-of-bounds"):
        validate_anomaly_thresholds([-5.0, 120.0])
