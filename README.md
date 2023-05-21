# GLaDOS Text-to-speech (TTS) Voice Generator

[![Build Status](https://jenkins.sudo.is/buildStatus/icon?job=ben%2Fglados-tts%2Fmain&style=flat-square)](https://jenkins.sudo.is/job/ben/job/glados-tts/)
[![git](https://git.sudo.is/shieldsio/static/v1?label=git&message=git.sudo.is/ben/glados-tts&logo=gitea&style=flat-square&logoWidth=20&color=darkgreen)](https://git.sudo.is/ben/glados-tts)
[![github](https://git.sudo.is/shieldsio/static/v1?label=github&message=benediktkr/glados-tts&logo=github&style=flat-square&logoWidth=20&color=darkgreen)](https://github.com/benediktkr/glados-tts)
[![MIT](https://git.sudo.is/shieldsio/badge/license-MIT-blue?style=flat-square)](LICENSE)

Neural network based TTS Engine.

## Description
The initial, regular Tacotron model was trained first on LJSpeech, and
then on a heavily modified version of the [Ellen
McClain](https://en.wikipedia.org/wiki/Ellen_McLain) dataset (all
non-Portal 2 voice lines removed, punctuation added).

* The Forward Tacotron model was only trained on about 600 voice lines.
* The HiFiGAN model was generated through transfer learning from the sample.
* All models have been optimized and quantized.

## Notes about this fork

Forked by [`ben`](https://git.sudo.is/ben) (:github: [`@benediktkr`](https://github.com/benediktkr)) from
[`github:VRCWizard/glados-tts-voice-wizard`](https://github.com/VRCWizard/glados-tts-voice-wizard),
which in turn was a fork of
[`github:R2D2FISH/glados-tts`](https://github.com/R2D2FISH/glados-tts).

This fork modernizes and improves the Python code in the project and does a bunch of housekeeping.

* `[DONE]`: Gets rid of the `SciPy` dependency (replaced with the more modern and lightwight [`pysoundfile`](https://github.com/gooofy/py-espeak-ng) (since all it was used for was writing a `.wav` file to disk)
* `[DONE]`: Support modern stable Python 3 versions, and update dependencies.
* `[DONE]`: Versioned packages with `poetry` and `pyproject.toml`
* `[DONE]`: Configuration handling with `click`.
* `[DONE]`: Better logging with `loguru`
* `[DONE]`: Python coding style and code quality improvements (proper handling of `file` object, improved logging..)
* `[DONE]`: Switch to using ASGI with `uvicorn` and `fastapi` instead of Flask and WSGI, and support production-capable deployments as default.
* `[DONE]`: Docker support
* `[TODO]`: Support Home Assistant through the [`notify` integration](https://www.home-assistant.io/integrations/notify/)
* `[TODO]`: see if its possible to avoid `espeak-ng` as a system package dependency (python bindings, buliding the C library, etc)

No work on the speech model itself is expected.

## Install

First you need to [install the `espeak-ng` system
packages](https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md).

```shell
# for debian/ubuntu:
sudo apt-get install espeak-ng

# for fedora/amazon:
sudo yum install espeak-ng
```

This can hopefully be improved in the future. There is a Python
bindings for `espeak` (at a glance, found
[`py-espeak-ng`](https://github.com/gooofy/py-espeak-ng)).

Then install the poetry-managed virtualenv

```shell
poetry install
```


## Usage

If you want to just play around with the TTS, works on the shell:

```shell
poetry run gladosctl
```

The TTS engine can also run as a web server:

```shell
poetry run gladosctl restapi
```

A public instance of the http api is running at `http://www.sudo.is/api/glados`, where you can also read [api documentation](https://www.sudo.is/api/glados/docs). 

![chell](chell.jpg)
