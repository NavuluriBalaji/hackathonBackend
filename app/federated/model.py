import numpy as np

class DemandModel:
    """
    Linear Trend & Demand Model for local district training.
    Parameters W (slope) and B (intercept) represent demand velocity and baseline.
    """
    def __init__(self, in_features: int = 1):
        self.w = np.random.randn(in_features, 1) * 0.01
        self.b = np.zeros((1, 1))

    def get_weights(self):
        return [self.w, self.b]

    def set_weights(self, weights):
        self.w = weights[0]
        self.b = weights[1]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.dot(X, self.w) + self.b

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 5, lr: float = 0.001):
        """Simple SGD optimization loop with feature normalization for local district training."""
        n_samples = len(X)
        if n_samples == 0:
            return 0.0
        
        # Feature normalization
        x_mean = np.mean(X) if np.std(X) > 0 else 0.0
        x_std = np.std(X) if np.std(X) > 0 else 1.0
        X_norm = (X - x_mean) / x_std

        y_mean = np.mean(y) if np.std(y) > 0 else 0.0
        y_std = np.std(y) if np.std(y) > 0 else 1.0
        y_norm = (y - y_mean) / y_std

        y_norm = y_norm.reshape(-1, 1)
        for _ in range(epochs):
            y_pred = np.dot(X_norm, self.w) + self.b
            dw = (1 / n_samples) * np.dot(X_norm.T, (y_pred - y_norm))
            db = (1 / n_samples) * np.sum(y_pred - y_norm)
            self.w -= lr * dw
            self.b -= lr * db

        y_pred = np.dot(X_norm, self.w) + self.b
        loss = float(np.mean((y_pred - y_norm) ** 2))
        return loss
