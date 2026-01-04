from transformers import pipeline
import pickle
from huggingface_hub import hf_hub_download
import torch

MODEL_ID = "HoangVanDuc/math-classifier-edai"

_clf = None
_label_encoder = None

def get_model():
    global _clf, _label_encoder

    if _clf is None:
        _clf = pipeline(
            "text-classification",
            model=MODEL_ID,
            device=-1,
            torch_dtype=torch.float16
        )

        label_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename="label_encoder.pkl"
        )

        with open(label_path, "rb") as f:
            _label_encoder = pickle.load(f)

    return _clf, _label_encoder


def classify_domain(text: str) -> str:
    clf, label_encoder = get_model()
    pred = clf(text)[0]
    label_id = int(pred["label"].split("_")[-1])
    return label_encoder.inverse_transform([label_id])[0]
