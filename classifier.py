# classifier.py
from transformers import pipeline
import pickle

clf = pipeline(
    "text-classification",
    model="./math_classifier",
    tokenizer="./math_classifier",
    device=-1  # CPU
)

with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

def classify_domain(text: str) -> str:
    pred = clf(text)[0]
    label_id = int(pred["label"].split("_")[-1])
    return label_encoder.inverse_transform([label_id])[0]
