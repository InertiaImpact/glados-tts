import sys
import json
import os

from soundfile import available_formats as audio_available_formats
from loguru import logger
import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand, version_option
import uvicorn

import glados_tts
import glados_tts.restapi
from glados_tts.engine import GLaDOS


DEFAULT_GLADOS_CONFIG = "glados.json"
CONTEXT_SETTINGS = {
    "max_content_width": 200,
    "terminal_width": 120,
    "auto_envvar_prefix": "GLADOS",
    "show_default": True,
    "color": True,
    # gets populated by GladosConfig.read_config_file, and in turn
    # populates/overwrites default values of cmdline options, working
    # as a way to use a config file
    "default_map": {}
}

def read_config_file(ctx, param, value):
    print("read_config_file callback")
    try:
        with open(value, 'r') as f:
            config = json.load(f)
            ctx.default_map.update(config)
    except FileNotFoundError:
        logger.error(f"file not found: '{value}', no config file loaded")
        config = {}

    return value


@click.group(
    cls=HelpColorsGroup,
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=False,
    help_headers_color="yellow",
    help_options_color="green",
)
@click.help_option(is_eager=True)
@click.option(
    "-c", "--config",
    type=click.Path(dir_okay=False),
    help="read config options from file\n",
    callback=read_config_file,
    is_eager=True,
    expose_value=False,
    show_envvar=True,
    show_default=True,
    default=DEFAULT_GLADOS_CONFIG
)
@click.option(
    "--debug/--no-debug",
    show_envvar=True,
    default=False
)
@click.option(
    "--log-level",
    show_envvar=True,
    default="INFO"
)
@click.option(
    "--audio-dir",
    type=click.Path(dir_okay=True),
    help="where generated audiofiles get saved",
    default="audio/",
    show_default=True,
    show_envvar=True
)
@click.option(
    "--audio-format",
    type=click.Choice(audio_available_formats(), case_sensitive=False),
    default="mp3",
    show_envvar=True,
    show_default=True
)
@click.option(
    "--fname-prefix",
    help="saved audio files are prefixed with this string",
    default="GLaDOS-tts",
    show_envvar=True
)
@click.option(
    "--env", type=click.Choice(['dev', 'prod']),
    default="prod",
    show_envvar=True,
    show_default=True,
    required=True
)
@version_option(
    prog_name=glados_tts.__name__,
    version=glados_tts.__version__,
    version_color="yellow",
    prog_name_color="green"
)
@click.pass_context
def cli(ctx, *args, **kwargs):
    ctx.meta.update(ctx.params)

    glados = GLaDOS.get()
    glados.start(kwargs['audio_dir'], kwargs['audio_format'], kwargs['fname_prefix'])


@cli.command(name="restapi")
@click.option("--host", default="127.0.0.1", show_envvar=True, show_default=True)
@click.option("--port", default="8124", type=int, show_envvar=True, show_default=True)
@click.option("--root-path", default="", show_envvar=True, show_default=True)
@click.option("--forwarded-allow-ips", default="127.0.0.1", show_envvar=True, show_default=True)
@click.option("--workers", default=1, show_envvar=True, show_default=True)
@click.pass_context
def cli_gladosapi(ctx, host, port, root_path, forwarded_allow_ips, workers):
    config = uvicorn.Config(
        "glados_tts.restapi:create_app",
        host=host,
        port=port,
        root_path=root_path,
        log_level=ctx.meta.get("log_level").lower(),
        proxy_headers=True,
        forwarded_allow_ips=forwarded_allow_ips,
        workers=workers,
        factory=True
    )
    server = uvicorn.Server(config)
    server.run()


def main():
    # load config and stuff here?
    cli()
