
from sklearn.ensemble import IsolationForest

# Example traffic that looks ordinary
# Each row: [requests per minute, errors per minute]
normal_traffic = [
    [3, 0],
    [5, 1],
    [7, 1],
    [4, 0],
    [8, 2],
    [6, 0],
    [2, 0],
    [9, 1],
    [5, 0],
    [7, 2],
]

# Create the ML model
model = IsolationForest(
    contamination=0.1,
    random_state=42
)

# Let the model learn from the examples
model.fit(normal_traffic)

# Test different traffic patterns
test_traffic = [
    [1, 0],
    [3, 0],
    [5, 1],
    [10, 1],
    [45, 20],
    [60, 30],
]

# Ask the model to classify the examples
predictions = model.predict(test_traffic)

# Display the predictions
for traffic, prediction in zip(test_traffic, predictions):
    requests, errors = traffic

    if prediction == 1:
        result = "Normal-looking traffic"
    else:
        result = "Unusual traffic"

    print(
        f"Requests: {requests}, "
        f"Errors: {errors} -> {result}"
    )

