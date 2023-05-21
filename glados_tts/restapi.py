from urllib.parse import urljoin

from typing import Annotated

from loguru import logger
from fastapi import FastAPI, APIRouter, Depends, Body, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from click.decorators import pass_meta_key

from glados_tts import __version__
from glados_tts.utils.tools import iterfile
from glados_tts.engine import GLaDOS
from glados_tts.models import GLaDOSResponse, GLaDOSRequest, HealthResponse, MaryRequest
from glados_tts.openapi.docs import create_docs_router


# import glados_tts.engine

audio_responses = {200: {"content": {a: {} for a in GLaDOS.audio_mimetypes}}}

def create_glados_router(root_path=""):
    router = APIRouter(prefix=root_path)
    glados = GLaDOS.get()


    @router.post(
        "/tts",
        summary="Text-to-speech",
        response_description="a `GLaDOSReponse` json-dict, mainly with the url to get the audiofile",
    )
    async def tts(params: Annotated[GLaDOSRequest, Body(embed=False)]) -> GLaDOSResponse:
        """Synthesize TTS audio with the GLaDOS engine
        """

        return glados.tts(
            params.text,
            use_cache=params.use_cache,
            audio_format=params.audio_format
        )

    @router.get("/tts", summary="Text-to-speech", response_description="Robot voice")
    async def tts_query(params: GLaDOSRequest = Depends()) -> GLaDOSResponse:
        return glados.tts(
            params.text,
            use_cache=params.use_cache,
            audio_format=params.audio_format
        )

    @router.get(
        "/say",
        summary="Text-to-speech (direct to audiofile)",
        response_description="an audiofile with the TTS audio",
        response_class=StreamingResponse,
        responses=audio_responses,
    )
    @router.get("/say.{audio_format}", include_in_schema=False)
    async def say(params: GLaDOSRequest = Depends()) -> StreamingResponse:
        """Synthesize TTS audio with the GLaDOS engine and directly return the
        audio file. Request parameters have the same meaning as for `/tts`.
        """

        g = glados.tts(params.text, use_cache=params.use_cache, audio_format=params.audio_format)
        audiofile_path = glados.get_audiofile_path(g.audio_filename)

        return StreamingResponse(
            iterfile(audiofile_path),
            media_type=g.audio_mimetype,
            headers={'GLaDOS-from-cache': str(g.from_cache)}
        )

    @router.get(
        "/audio/{audio_filename}",
        summary="Fetch a generated TTS audio file.",
        response_description="the requested audiofile `filename`.",
        response_class=FileResponse,
        responses=audio_responses,
    )
    async def audio(audio_filename: str) -> FileResponse:
        """Get an audio file that has been synthesized, using
        the `audio_filename` returned from `/tts`.
        """

        return FileResponse(
            glados.get_audiofile_path(audio_filename),
            filename=audio_filename
        )

    return router

def create_mary_router(root_path=""):
    router = APIRouter(prefix=root_path)
    glados = GLaDOS.get()

    @router.post(
        "/process",
        summary="Basic support for the Mary TTS API",
        response_description="an audiofile with the TTS audio",
        response_class=StreamingResponse,
        responses=audio_responses,
    )
    async def say(params: MaryRequest) -> StreamingResponse:
        """Accept the same format as the `/process` endpoint on the HTTP API
        for [MARY TTS system](https://marytts.github.io/) system, and
        synthesize TTS audio with the GLaDOS engine.

        This endpoint returns the audiofile directly, and works the same as
        the `/say` endpoint does.

        Reference: [`github:Poeschl/speak2mary`](https://github.com/Poeschl/speak2mary)

        """

        g = glados.tts(params.INPUT_TEXT, use_cache=True, audio_format="wav")
        audiofile_path = glados.get_audiofile_path(g.audio_filename)

        return StreamingResponse(
            iterfile(audiofile_path),
            media_type=g.audio_mimetype,
            headers={'GLaDOS-from-cache': str(g.from_cache)}
        )

    return router

@pass_meta_key('restapi')
def create_app(restapi_config):
    app = FastAPI(
        title="GLaDOS Text-to-speech API",
        description="Generate audiofiles that sound like GLaDOS.\n\n api docs: [swagger](swagger) | [redoc](redoc)",
        version=__version__,
        license_info={"name": "MIT", "url": "https://en.wikipedia.org/wiki/MIT_License"},
        openapi_tags=[
            {"name": "api", "description": "operations for the GLaDOS TTS API itself"},
            {"name": "tts", "description": "Text-to-speech API"},
            {"name": "mary", "description": "Basic compatability interface the HTTP API for [MARY TTS](https://marytts.github.io/)."}
        ],
        root_path = restapi_config.get('root_path', ''),
        openapi_url="/openapi.json",
        swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
        docs_url=None,
        redoc_url=None,
    )

    docs_router = create_docs_router(app.openapi_url)
    app.include_router(docs_router, prefix="/docs")

    glados_router = create_glados_router()
    app.include_router(glados_router, tags=['tts'])

    mary_router = create_mary_router()
    app.include_router(mary_router, prefix='/mary', tags=['mary'])


    @app.get("/", include_in_schema=False)
    async def index(request: Request):
        return {
            "info": "a http json api for GLaDOS Text-to-speech",
            "docs_url": app.url_path_for('docs_index'),
            "root_path": request.scope.get("root_path"),
            "root_path_in_config": app.root_path
        }

    @app.get("/health", summary="Healthcheck", response_description="Healthcheck results", tags=["api"])
    async def health() -> HealthResponse:
        """The healthcheck for the GLaDOS TTS Rest API.
        """
        return {"status": "healthy"}


    route_summaries = []
    for item in app.routes:
        methods = ", ".join(item.methods)
        route_summaries.append(f" - {methods.ljust(10)} > {item.path}")
    route_summary = "\n".join(route_summaries)
    logger.debug(f"routes:\n{route_summary}")
    logger.debug(app.root_path)
    return app
