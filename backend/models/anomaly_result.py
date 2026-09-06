class AnomalyResult:

    def __init__(
        self,
        anomaly,
        anomaly_type,
        feature,
        value,
        timestamp,
        reason,
        station_id=None
    ):

        self.anomaly = anomaly
        self.anomaly_type = anomaly_type
        self.feature = feature
        self.value = value
        self.timestamp = timestamp
        self.reason = reason
        self.station_id = station_id