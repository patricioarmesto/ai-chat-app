from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

OLLAMA_URL = "http://ollama:11434/api/chat"
MODEL = "llama2"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": request.message}
        ],
        "stream": False
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            # The response is in data['message']['content']
            return ChatResponse(response=data.get("message", {}).get("content", ""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 