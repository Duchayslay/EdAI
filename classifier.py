# classifier.py
from transformers import pipeline
import pickle
from huggingface_hub import hf_hub_download

MODEL_ID = "HoangVanDuc/math-classifier-edai"

# ép CPU (Render không có GPU)
clf = pipeline(
    "text-classification",
    model=MODEL_ID,
    device=-1
)

# tải label encoder từ HuggingFace Hub
label_path = hf_hub_download(
    repo_id=MODEL_ID,
    filename="label_encoder.pkl"
)

with open(label_path, "rb") as f:
    label_encoder = pickle.load(f)

def classify_domain(text: str) -> str:
    pred = clf(text)[0]
    label_id = int(pred["label"].split("_")[-1])
    return label_encoder.inverse_transform([label_id])[0]

