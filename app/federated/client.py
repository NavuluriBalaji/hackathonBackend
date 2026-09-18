import flwr as fl
import numpy as np
from typing import List, Dict, Tuple
from app.federated.model import DemandModel

class DistrictFlowerClient(fl.client.NumPyClient):
    """
    Isolated District Client Node for Federated Learning.
    Trains locally on district database logs and returns only model weights (W, B).
    """
    def __init__(self, district_id: str, X: np.ndarray, y: np.ndarray):
        self.district_id = district_id
        self.X = X
        self.y = y
        self.model = DemandModel()

    def get_parameters(self, config: Dict[str, str]) -> List[np.ndarray]:
        """Returns local model weights to the central aggregator."""
        return self.model.get_weights()

    def fit(self, parameters: List[np.ndarray], config: Dict[str, str]) -> Tuple[List[np.ndarray], int, Dict]:
        """
        Receives global model weights, updates local model, 
        trains locally on district data, and returns updated weights + sample size.
        """
        self.model.set_weights(parameters)
        loss = self.model.fit(self.X, self.y, epochs=5, lr=0.01)
        num_samples = len(self.X)
        return self.model.get_weights(), num_samples, {"loss": loss, "district_id": self.district_id}

    def evaluate(self, parameters: List[np.ndarray], config: Dict[str, str]) -> Tuple[float, int, Dict]:
        """Evaluates local loss against global parameters."""
        self.model.set_weights(parameters)
        y_pred = self.model.predict(self.X)
        loss = float(np.mean((y_pred - self.y.reshape(-1, 1)) ** 2)) if len(self.X) > 0 else 0.0
        return loss, len(self.X), {"district_id": self.district_id}
