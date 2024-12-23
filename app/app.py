from fastapi import FastAPI
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import sqlite3
import os
# Initialize FastAPI app
app = FastAPI()

# Initialize SQLite database connection
DB_PATH = 'transcriptions.db'  # Read from environment variable

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                request_id TEXT PRIMARY KEY,
                transcript TEXT,
                channel_index INTEGER,
                num_channels INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration FLOAT
            )
        """)
        conn.commit()

# Run database initialization
init_db()

class Word(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class Alternative(BaseModel):
    transcript: str
    confidence: float
    words: List[Word]

class Channel(BaseModel):
    alternatives: List[Alternative]

class ModelInfo(BaseModel):
    name: str
    version: str
    arch: str

class Metadata(BaseModel):
    request_id: str
    model_info: ModelInfo
    model_uuid: str

class TranscriptionData(BaseModel):
    type: str = Field(..., description="Type of transcription data")
    channel_index: List[int]
    duration: float
    start: float
    is_final: bool
    speech_final: bool
    channel: Channel
    metadata: Metadata
    from_finalize: Optional[bool] = False

    @validator("channel_index")
    def validate_channel_index(cls, v):
        if not all(isinstance(i, int) for i in v):
            raise ValueError("channel_index must contain only integers")
        return v
@app.get("/health")
async def health():
    """
    Health check endpoint to ensure the service is up and running.
    """
    return {"status": "ok"}

@app.post("/")
async def process_transcription(data: TranscriptionData):
    """
    Processes transcription data received from a POST request
    and saves it to SQLite.

    Args:
        data: The transcription data conforming to the TranscriptionData model.

    Returns:
        A dictionary containing the extracted transcript.
    """
    # Extract transcript
    if data.type == "Results":
        transcript = data.channel.alternatives[0].transcript

        if not transcript:
            transcript = "No transcript available."
            return {"message": transcript}
        if not data.speech_final:
            return {"message": "Speech is not finalized yet. Waiting for more data."}
        # Save to SQLite
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO transcriptions (request_id, transcript, channel_index, num_channels, duration)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data.metadata.request_id,
                transcript,
                data.channel_index[0],
                data.channel_index[1],
                data.duration,
            ))
            conn.commit()
    else:
        transcript = "No transcript available."
        return {"message": transcript}

    return {"message": "Transcription processed and saved to SQLite.", "transcript": transcript}
