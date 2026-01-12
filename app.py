import os
import requests
import gradio as gr
from fastapi import FastAPI, Request
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

fastapi_app = FastAPI()

# ---------- Telegram webhook ----------
@fastapi_app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    if "message" not in data:
        return {"ok": True}
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": f"You said: {text}"}
    )
    return {"ok": True}

# ---------- Gradio ----------
def gradio_reply(text):
    return f"You said: {text}"

demo = gr.Interface(
    fn=gradio_reply,
    inputs=gr.Textbox(label="Message"),
    outputs=gr.Textbox(label="Reply"),
    title="Telegram + Gradio Bot"
)

# Mount Gradio to FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

# ---------- Run server ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

