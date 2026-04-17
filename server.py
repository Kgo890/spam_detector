from flask import Flask
from flask_socketio import SocketIO, emit
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# -----------------------------
# Load ML Model
# -----------------------------
MODEL_DIR = "./final_spam_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

def predict_spam(text: str):
    """
    Returns:
        spam (bool)
        confidence (float: 0-100)
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128
    ).to(device)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=1)[0]  # [not_spam, spam]

    spam_conf = float(probs[1]) * 100
    spam = spam_conf >= 50  # threshold (change if you want)

    return spam, spam_conf

# -----------------------------
# Flask SocketIO Server
# -----------------------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return "Spam Detector Server Running."

# -----------------------------
# SOCKET EVENT: client sends message
# -----------------------------
@socketio.on("send_message")
def handle_send_message(data):
    """
    Expected data:
    {
        "username": "Kaden",
        "message": "hello world"
    }
    """
    username = data.get("username")
    text = data.get("message", "")

    # apply ML model
    is_spam, confidence = predict_spam(text)

    # Build response
    payload = {
        "username": username,
        "message": text,
        "is_spam": is_spam,
        "confidence": round(confidence, 2)
    }

    # Broadcast to ALL clients
    emit("receive_message", payload, broadcast=True)

    print(f"[MSG] {username}: {text}")
    print(f"      spam={is_spam} ({confidence:.2f}%)")

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    print("Server running on http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
