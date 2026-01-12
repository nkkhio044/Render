import os
import requests
import gradio as gr
from fastapi import FastAPI, Request
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

def llm_reply(text):
    if not HF_API_KEY:
        return f"You said: {text}"

    r = requests.post(
        HF_URL,
        headers=HF_HEADERS,
        json={"inputs": text},
        timeout=30
    )

    if r.status_code != 200:
        return "⚠️ Model busy, try again"

    return r.json()[0]["generated_text"]

# -------- FASTAPI --------
app_fastapi = FastAPI()

@app_fastapi.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    reply = llm_reply(text)

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )
    return {"ok": True}

# -------- GRADIO --------
demo = gr.Interface(
    fn=llm_reply,
    inputs=gr.Textbox(),
    outputs=gr.Textbox(),
    title="Telegram + HF Free Bot"
)

app = gr.mount_gradio_app(app_fastapi, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
