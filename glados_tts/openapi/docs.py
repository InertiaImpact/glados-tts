import os
from pkg_resources import resource_filename

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates


def create_docs_router(openapi_url):
    router = APIRouter()
    templates = Jinja2Templates(directory=resource_filename(__name__, "jinja"))

    async def _template_doc(item: str, request: Request):
        t = Jinja2Templates(directory=resource_filename(__name__, "jinja"))
        return t.TemplateResponse(f"{item}.j2", {
            "request": request,
            "openapi_url": request.url_for('openapi').path, #openapi_url,
            "static_url": request.url_for('static').path
        })

        return

    @router.get("/static", include_in_schema=False)
    async def static():
        return ""

    @router.get("/static/{filename}", include_in_schema=False)
    async def static_file(filename: str) -> FileResponse:
        return FileResponse(
            resource_filename(__name__,  os.path.join("static", filename)),
            filename=filename
        )

    @router.get("/redoc", include_in_schema=False)
    async def redoc_html(request: Request) -> HTMLResponse:
        redoc = await _template_doc("redoc.html", request=request)
        return redoc


    @router.get("/", include_in_schema=False, name='docs_index')
    @router.get("/swagger", include_in_schema=False)
    async def swagger_html(request: Request) -> HTMLResponse:
        swagger = await _template_doc("swagger.html", request=request)
        return swagger


    @router.get("/oauth2-redirect", include_in_schema=False)
    async def oauth2_redirect_html(request: Request) -> HTMLResponse:
        oauth_redirect = await _template_doc("oauth2-redirect.html", request=request)
        return oauth_redirect


    return router
