import json
import os
from functools import update_wrapper

from loguru import logger
import click
from click_help_colors import HelpColorsGroup, version_option
import uvicorn
from fastapi import FastAPI

import glados_tts
import glados_tts.restapi
from glados_tts.engine import GLaDOS

import click

# Check for the correct environment variable based on the operating system
home_dir = os.environ.get("HOME") or os.environ.get("USERPROFILE")
if not home_dir:
    raise EnvironmentError("Neither 'HOME' nor 'USERPROFILE' environment variables are set.")

DEFAULT_GLADOS_CONFIG = os.path.join(home_dir, ".config", "glados.json")


@click.command()
@click.pass_context
def cli(ctx):
    # Make sure `ctx.meta` is initialized as a dict
    ctx.ensure_object(dict)

    # Safely get the log level and provide a default value
    log_level = (ctx.meta.get("log_level") or "INFO").lower()


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
    try:
        with open(value, 'r') as f:
            config = json.load(f)
        ctx.default_map.update(config)
        ctx.meta.update(config)
    except json.decoder.JSONDecodeError as e:
        logger.error(e)
        raise SystemExit from e

    except FileNotFoundError:
        logger.error(f"file not found: '{value}', no config file loaded")
        config = {}

    return value

def update_meta(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        if ctx.info_name == "gladosctl":
            ctx.meta.update(ctx.params)
        else:
            ctx.meta.setdefault(ctx.info_name, {})
            ctx.meta[ctx.info_name].update(ctx.params)

        return ctx.invoke(f, *args, **kwargs)
    return update_wrapper(new_func, f)

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
@click.option("--debug/--no-debug", default=False, show_envvar=True, show_default=True)
@click.option("--log-level", show_envvar=True, show_default=True, default="INFO")
@click.option(
    "--audio-dir", default="audio/", show_default=True, show_envvar=True,
    type=click.Path(dir_okay=True),
    help="where generated audiofiles get saved",
)
@click.option(
    "--audio-format", default="wav", show_default=True, show_envvar=True,
    type=click.Choice(GLaDOS.audio_formats, case_sensitive=False),
)
@version_option(
    prog_name=glados_tts.__name__, version=glados_tts.__version__,
    version_color="yellow", prog_name_color="green"
)
@update_meta
@click.pass_context
def cli(ctx, *args, **kwargs):
    glados = GLaDOS.get()
    glados.start(kwargs['audio_dir'], kwargs['audio_format'])


@cli.command(name="restapi")
@click.option("--host", default="127.0.0.1", show_envvar=True, show_default=True)
@click.option("--port", default="8124", type=int, show_envvar=True, show_default=True)
@click.option("--root-path", default="", show_envvar=True, show_default=True)
@click.option("--forwarded-allow-ips", default="127.0.0.1", show_envvar=True, show_default=True)
@click.option("--workers", default=1, show_envvar=True, show_default=True)
@update_meta
@click.pass_context
def cli_gladosapi(ctx, host, port, root_path, forwarded_allow_ips, workers):
    debug_mode = ctx.meta.get("debug", False)
    log_level = ctx.meta.get("log_level", "INFO").lower()  # Safely handle NoneType by providing a default value
    
    if root_path != "":
        logger.warning(f'path="{root_path}"')

    config = uvicorn.Config(
        "glados_tts.restapi:create_app",
        host=host,
        port=port,
        log_level=log_level,
        proxy_headers=True,
        forwarded_allow_ips=forwarded_allow_ips,
        reload=debug_mode,
        workers=workers if not debug_mode else None,
        factory=True,
        root_path=root_path
    )
    server = uvicorn.Server(config)
    server.run()



def main():
    # load config and stuff here?
    cli()
