import os
import json
from fastapi import FastAPI, Request, HTTPException, Response
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = FastAPI()

# Discord gives you a Public Key in your Developer Portal
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "YOUR_PUBLIC_KEY_HERE")

def verify_signature(body: bytes, signature: str, timestamp: str):
    try:
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False

@app.post("/interactions")
async def interactions(request: Request):
    # 1. Get raw request elements
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = await request.body()

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signatures")

    # 2. Verify it is actually Discord calling
    if not verify_signature(body, signature, timestamp):
        raise HTTPException(status_code=401, detail="Invalid request signature")

    # 3. Parse JSON data
    data = json.loads(body.decode("utf-8"))
    
    # Type 1: Discord PING verification check
    if data.get("type") == 1:
        return {"type": 1}

    # Type 2: A User typed a Slash Command
    if data.get("type") == 2:
        command_name = data.get("data", {}).get("name")
        
        if command_name == "hello":
            return {
                "type": 4, # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": "um hi"
                }
            }

    return HTTPException(status_code=400, detail="Unknown interaction type")
