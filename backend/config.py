SPIKE_THRESHOLDS = {

    "temperature": 5.0,
    "humidity": 15.0,
    "pressure": 10.0,
    "wind_speed": 10.0,
    "rainfall": 20.0,

}


DRIFT_CONFIG = {

    "temperature": {
        "baseline_window": 5,
        "recent_window": 5,
        "threshold": 2.0,
    },

    "humidity": {
        "baseline_window": 5,
        "recent_window": 5,
        "threshold": 5.0,
    },

    "pressure": {
        "baseline_window": 5,
        "recent_window": 5,
        "threshold": 5.0,
    },

    "wind_speed": {
        "baseline_window": 5,
        "recent_window": 5,
        "threshold": 5.0,
    },

    "rainfall": {
        "baseline_window": 5,
        "recent_window": 5,
        "threshold": 5.0,
    },

}