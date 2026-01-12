import os
import requests
import gradio as gr
from fastapi import FastAPI, Request
import uvicorn
from transformers import pipeline

# ----------------- SECRETS -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram bot token
HF_API_KEY = os.getenv("HF_API_KEY")  # Hugging Face API key

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")
if not HF_API_KEY:
    print("HF_API_KEY missing, fallback to echo bot")

# ----------------- LLM FUNCTION -----------------
# Using HF text-generation model
def llm_reply(text):
    if not HF_API_KEY:
        # fallback: echo bot
        return f"You said: {text}"

    # Initialize generator (small model recommended for free tier)
    generator = pipeline(
        "text-generation",
        model="TheBloke/vicuna-7B-1.1-HF",  # Free Hugging Face model
        use_auth_token=HF_API_KEY
    )
    output = generator(text, max_new_tokens=100)
    return output[0]['generated_text']

# ----------------- FASTAPI APP -----------------
app_fastapi = FastAPI()

@app_fastapi.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    reply_text = llm_reply(text)

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply_text}
    )
    return {"ok": True}

# ----------------- GRADIO INTERFACE -----------------
def gradio_fn(text):
    return llm_reply(text)

demo = gr.Interface(
    fn=gradio_fn,
    inputs=gr.Textbox(label="Type your message"),
    outputs=gr.Textbox(label="Reply"),
    title="Telegram + HuggingFace Bot"
)

# Mount Gradio to FastAPI
app = gr.mount_gradio_app(app_fastapi, demo, path="/")

# ----------------- RUN SERVER -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
