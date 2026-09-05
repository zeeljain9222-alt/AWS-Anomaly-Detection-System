from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AnomalyResult:
    """
    Standard output format for the M3 Rule Engine.

    This object is passed from M3 to M4.
    """

    anomaly: bool
    anomaly_type: str
    feature: Any
    value: Optional[float]
    timestamp: Any
    reason: str

    def to_dict(self):
        """
        Convert the anomaly result into a dictionary.
        """

        return {
            "anomaly": self.anomaly,
            "anomaly_type": self.anomaly_type,
            "feature": self.feature,
            "value": self.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }