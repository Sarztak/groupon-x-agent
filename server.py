import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from router import handle_mention

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

CATALOG_PATH   = Path("./deals_catalog.json").resolve()
PROMPTS_DIR    = Path("./prompts").resolve()
REFERENCES_DIR = Path("./prompts/references").resolve()


class MentionRequest(BaseModel):
    message: str
    username: str


@app.post("/api/mention")
async def mention(req: MentionRequest):
    result = handle_mention(
        req.message,
        req.username,
        CATALOG_PATH,
        PROMPTS_DIR,
        REFERENCES_DIR,
    )
    return result
