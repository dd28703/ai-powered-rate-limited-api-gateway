
import logging
import time
from collections import defaultdict, deque

from sklearn.ensemble import IsolationForest

logger = logging.getLogger("api_gateway")

# Illustrative examples of ordinary traffic:
# [requests in 60 seconds, errors in 60 seconds]
normal_traffic = [
    [2, 0],
    [3, 0],
    [4, 0],
    [5, 0],
    [6, 0],
    [3, 1],
    [4, 1],
    [5, 1],
    [6, 1],
    [4, 0],
    [5, 0],
    [6, 0],
    [3, 0],
    [4, 1],
    [5, 1],
]

model = IsolationForest(
    contamination=0.1,
    random_state=42
)

model.fit(normal_traffic)

WINDOW_SECONDS = 60

# Each client gets its own history of request times and status codes.
traffic_history = defaultdict(deque)


def analyze_ml_traffic(client_id: str, status_code: int):
    current_time = time.time()
    history = traffic_history[client_id]

    # Record this request.
    history.append((current_time, status_code))

    # Remove requests older than 60 seconds.
    while (
        history
        and current_time - history[0][0] >= WINDOW_SECONDS
    ):
        history.popleft()

    # Build the two features for the model.
    request_count = len(history)
    error_count = sum(
        1 for _, code in history if code >= 400
    )
    # Wait for enough observations before classifying traffic.
    if request_count < 5:
        return

    features = [[request_count, error_count]]
    prediction = model.predict(features)[0]

    if prediction == -1:
        logger.warning(
            "ML anomaly alert: client=%s requests=%s errors=%s "
            "window_seconds=%s",
            client_id,
            request_count,
            error_count,
            WINDOW_SECONDS,
        )
