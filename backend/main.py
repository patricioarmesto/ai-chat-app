from typing import Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

OLLAMA_URL = "http://ollama:11434/api/chat"
MODEL = "llama2"

# In-memory store for conversation history
conversations: Dict[str, List[dict]] = {}

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Retrieve or initialize conversation history
    history = conversations.get(request.conversation_id, [])
    # Add the new user message
    history.append({"role": "user", "content": request.message})
    payload = {
        "model": MODEL,
        "messages": history,
        "stream": False
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            # The response is in data['message']['content']
            assistant_message = data.get("message", {}).get("content", "")
            # Add assistant response to history
            history.append({"role": "assistant", "content": assistant_message})
            # Save updated history
            conversations[request.conversation_id] = history
            return ChatResponse(response=assistant_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 