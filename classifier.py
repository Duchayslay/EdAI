from transformers import pipeline
import pickle
from huggingface_hub import hf_hub_download
import os

MODEL_ID = "HoangVanDuc/math-classifier-edai"

_clf = None
_label_encoder = None


def load_resources():
    global _clf, _label_encoder

    if _clf is not None:
        return

    _clf = pipeline(
        "text-classification",
        model=MODEL_ID,
        device=-1,
        framework="pt",
        model_kwargs={
            "low_cpu_mem_usage": True
        }
    )

    label_path = hf_hub_download(
        repo_id=MODEL_ID,
        filename="label_encoder.pkl"
    )

    with open(label_path, "rb") as f:
        _label_encoder = pickle.load(f)


def classify_domain(text: str) -> str:
    if _clf is None:
        load_resources()

    pred = _clf(
        text,
        truncation=True,
        max_length=128   # ⬅️ RẤT QUAN TRỌNG
    )[0]

    label_id = int(pred["label"].split("_")[-1])
    return _label_encoder.inverse_transform([label_id])[0]
