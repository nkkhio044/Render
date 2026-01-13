import os
import requests
import gradio as gr
from fastapi import FastAPI, Request
import uvicorn

# ------------------ ENV ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

# ------------------ GROQ CONFIG ------------------
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def llm_reply(text: str) -> str:
    try:
        r = requests.post(
            GROQ_URL,
            headers=GROQ_HEADERS,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a helpful, friendly assistant."},
                    {"role": "user", "content": text}
                ]
            },
            timeout=20
        )

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return "⚠️ Server error, try again"

# ------------------ FASTAPI ------------------
app_fastapi = FastAPI()

@app_fastapi.post("/webhook")
async def telegram_webhook(req: Request):
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

# ------------------ GRADIO ------------------
demo = gr.Interface(
    fn=llm_reply,
    inputs=gr.Textbox(label="Type message"),
    outputs=gr.Textbox(label="Bot reply"),
    title="Telegram + Groq AI Bot"
)

app = gr.mount_gradio_app(app_fastapi, demo, path="/")

# ------------------ RUN ------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
app = gr.mount_gradio_app(app_fastapi, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
