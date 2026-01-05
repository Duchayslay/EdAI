import pickle
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import hf_hub_download

MODEL_ID = "HoangVanDuc/math-classifier-edai"

_tokenizer = None
_model = None
_label_encoder = None

def get_model():
    global _tokenizer, _model, _label_encoder

    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            use_fast=True
        )

        _model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True   # 🔥 CỰC QUAN TRỌNG
        )
        _model.eval()

        label_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename="label_encoder.pkl"
        )

        with open(label_path, "rb") as f:
            _label_encoder = pickle.load(f)

    return _tokenizer, _model, _label_encoder


@torch.inference_mode()  # 🔥 không tạo graph
def classify_domain(text: str) -> str:
    tokenizer, model, label_encoder = get_model()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=64    # 🔥 giảm RAM
    )

    outputs = model(**inputs)
    label_id = int(torch.argmax(outputs.logits, dim=-1))

    return label_encoder.inverse_transform([label_id])[0]
