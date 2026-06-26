"""Adapter — the bolt-on contract (INTEROP_SPEC §7).

adapter(backbone_embedding[H], experimental_feature[D]) -> conditioning[H]

This numpy reference is the *interface contract*, not a trained model. The enterprise/consumer keeps
their backbone FROZEN and trains only this thin adapter on their PRIVATE data, locally. The reference
weights here are deterministically seeded and UNTRAINED — they exist to validate shapes and the bolt-on,
not to make predictions. The production version is a torch module (frozen backbone + LoRA head); the
shapes and I/O are identical so it is a drop-in.

NOTE (anti-stub): nothing here is presented as a result. Weights are random-init reference only.
"""
from __future__ import annotations
import numpy as np


class Adapter:
    def __init__(self, backbone_dim: int = 1280, feature_dim: int = 48, seed: int = 0,
                 gate: float = 0.1, trained: bool = False):
        self.H = int(backbone_dim)
        self.D = int(feature_dim)
        self.gate = float(gate)
        self.trained = bool(trained)  # honest flag: False = reference/untrained
        rng = np.random.default_rng(seed)
        # projection D -> H (the only trainable part in production)
        self.W = (rng.standard_normal((self.H, self.D)) / np.sqrt(self.D)).astype(np.float32)
        self.b = np.zeros(self.H, dtype=np.float32)

    def __call__(self, backbone_embedding: np.ndarray, experimental_feature: np.ndarray) -> np.ndarray:
        e = np.asarray(backbone_embedding, dtype=np.float32).reshape(-1)
        f = np.asarray(experimental_feature, dtype=np.float32).reshape(-1)
        assert e.shape[0] == self.H, f"backbone_embedding must be length {self.H}, got {e.shape[0]}"
        assert f.shape[0] == self.D, f"experimental_feature must be length {self.D}, got {f.shape[0]}"
        proj = np.tanh(self.W @ f + self.b)             # conditioning signal in backbone space
        return (e + self.gate * proj).astype(np.float32)  # gated residual conditioning

    def trainable_params(self) -> int:
        return self.W.size + self.b.size

    def __repr__(self):
        return f"Adapter(H={self.H}, D={self.D}, params={self.trainable_params()}, trained={self.trained})"
