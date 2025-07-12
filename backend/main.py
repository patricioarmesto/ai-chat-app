from typing import Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import traceback  # Add for detailed error logging
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://ollama:11434/api/chat"
MODEL = "llama2"

# In-memory store for conversation history
conversations: Dict[str, List[dict]] = {}

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

class ChatResponse(BaseModel):
    response: str

@app.get("/ping", response_class=PlainTextResponse)
async def ping():
    return "pong"

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"Received /chat request: message={request.message}, conversation_id={request.conversation_id}")
    # Retrieve or initialize conversation history
    history = conversations.get(request.conversation_id, [])
    # Add the new user message
    history.append({"role": "user", "content": request.message})
    payload = {
        "model": MODEL,
        "messages": history,
        "stream": False
    }
    print(f"Payload to OLLAMA: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(OLLAMA_URL, json=payload, timeout=60)
            print(f"OLLAMA response status: {r.status_code}")
            print(f"OLLAMA response body: {r.text}")
            r.raise_for_status()
            data = r.json()
            # The response is in data['message']['content']
            assistant_message = data.get("message", {}).get("content", "")
            # Add assistant response to history
            history.append({"role": "assistant", "content": assistant_message})
            # Save updated history
            conversations[request.conversation_id] = history
            print(f"Returning assistant response: {assistant_message}")
            return ChatResponse(response=assistant_message)
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) 