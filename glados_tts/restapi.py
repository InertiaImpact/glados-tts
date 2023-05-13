from enum import Enum
from typing import Literal, Any, Annotated

from fastapi import FastAPI, Request, Query, Path
from pydantic import BaseModel, Field, Required
from loguru import logger

from glados_tts.engine import GLaDOS, GLaDOSTTSAudioModel
import glados_tts.engine

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class Health(BaseModel):
    status: Literal['healthy', 'unhealthy']

class Index(BaseModel):
    info: str
    root_path: str

class GLaDOSResponse(BaseModel):
    text: str

query_text = Query(title="Text-to-speech", description="The text that GLaDOS should speak")
query_cache = Query(
    title="cache enabled",
    description="use the cache of previously generated audio, or force the TTS engine to always generate new audio"
)



logger.info("hello from restapi")

def create_app():
    logger.info("creating app")
    app = FastAPI()
    glados = GLaDOS.get()

    @app.get("/", response_model=Index)
    async def index(request: Request):
        root_path = request.scope.get("root_path")

        return {"info": "GLaDOS tts", "root_path": root_path or ""}

    @app.get("/health")
    async def health() -> Health:
        #return Health(status=HealthStatus.HEALTHY)
        return Health(status="healthy")


    @app.get("/say")
    async def say(text: Annotated[str, query_text], use_cache: Annotated[bool, query_cache] = True) -> GLaDOSTTSAudioModel:
        r = glados.say(text, use_cache=use_cache)
        return r


    return app
