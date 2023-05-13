import io
import os
import hashlib
from time import time
from functools import lru_cache
from datetime import datetime
from typing import Optional

import torch
import soundfile
from loguru import logger
from pydantic import BaseModel, Field, FilePath

from glados_tts.utils import tools


class GLaDOSTTSAudioModel(BaseModel):
    from_cache: str = False
    text: str
    audiofile_name: str
    audiofile_path: Optional[FilePath]
    audiofile_timestamp: datetime


class GLaDOSError(Exception):
    pass


class GLaDOSInputError(GLaDOSError):
    pass


class GLaDOS:
    def __init__(self):
        self.started = False
        self.models_loaded = False

        self.device = self._select_device()
        logger.debug(f"selected device: '{self.device}'")

        self.audio_dir = ""
        self.fname_prefix = ""
        self.audio_format = ""

        # 22,05 kHz sample rate
        # TODO: should sample rate be a config value?
        self.sample_rate_khz = int(22050)

    def start(self, audio_dir, audio_format="mp3", fname_prefix="GLaDOS-", delay_generate_models=True):
        logger.debug(f"starting GLaDOS (dir: '{audio_dir}', prefix: {fname_prefix}, format: {audio_format})")
        self.audio_dir = audio_dir
        self.fname_prefix = fname_prefix
        self.audio_format = audio_format.lower()

        # TODO: fix relative paths
        self.glados = torch.jit.load('glados_tts/models/glados.pt')
        self.vocoder = torch.jit.load('glados_tts/models/vocoder-gpu.pt', map_location=self.device)

        if delay_generate_models:
            logger.info("models are not loaded and will be generated on the first request")
            self.models_loaded = False
        else:
            self._generate_models()
            self.models_loaded = True
        self.started = True


    @classmethod
    @lru_cache()
    def get(cls):
        logger.success("you got me")
        return cls()

    def get_tts_path(self, fname):
        return os.path.join(self.audio_dir, fname)

    def _generate_models(self):
        logger.info("generating models")
        # TODO: why 4?
        for i in range(4):
            prepared = tools.prepare_text(str(i))
            init = self.glados.generate_jit(prepared)
            init_mel = init['mel_post'].to(self.device)
            init_vo = self.vocoder(init_mel)

    def _prepare_text(f):
        def wrapped(self, text, *args, **kwargs):
            text_tensor = tools.prepare_text(text)
            return f(self, text, text_tensor, *args, **kwargs)
        return wrapped

    def _select_device(self):
        if torch.is_vulkan_available():
            return 'vulkan'
        elif torch.cuda.is_available():
            return 'cuda'
        else:
            return 'cpu'

    def _to_alnum(self, s):
        return "".join([a for a in s.replace(" ", "_") if a.isalnum() or a == "_"])

    def _short_name(self, text):
        """generate a "short name" for the input string. this gets used in log
        messages (to keep them meaningful and easy to read), as well
        as audio filenames.

        this is just a convenience method to get the first 7 words
        (since it gets called in multiple places, also ensures
        consistency)

        """

        return " ".join(text.split(" ")[:7])

    def _make_fname(self, text):
        """use the same "short name" as we do in logs, but only keeping alphanumeric
        characters and replacing whitespaces, for filesystem friendlyness.

        then we hash the full input string, and use the hex string for
        the hash to guarantee unique filenames.

        since we arent hashing for cryptographic reasons, i picked
        BLAKE2s with 20-bytes, somewhat arbitrarily, mostly because
        it's hex string is relatively short (nice for the filenames).

        the filename is structured as follows:
          ${CONFIG_FNAME_PREFIX}_${SHORT_ALNUM_NAME}_${HASH}.${EXTENSION}

        """

        text_name = self._short_name(text)
        base_fname = self._to_alnum(text_name)

        h = hashlib.blake2b(digest_size=20)
        h.update(text.encode())

        fname = f"{self.fname_prefix}_{base_fname}_{h.hexdigest()}.{self.audio_format}"

        return fname

    @_prepare_text
    def tts_generate_audio(self, text, text_tensor):
        if not self.models_loaded:
            self._generate_models()

        t0 = time()
        t_name = self._short_name(text)
        logger.debug(f"generating audio for text: '{text}'")

        with torch.no_grad():
            # Generate generic TTS-output
            tts_output = self.glados.generate_jit(text_tensor.to(self.device))

            # Use HiFiGAN as vocoder to make output sound like GLaDOS
            mel = tts_output['mel_post'].to(self.device)
            audio = self.vocoder(mel)

            logger.info(f"time to generate audio for '{t_name}': {round(time()-t0, 2)}s")

            # Normalize audio to fit in file
            audio = audio.squeeze() * 32768.0
            return audio.cpu().numpy().astype('int16')



    def tts_audio_to_file(self, text, use_cache=True):
        """generates the audio, writes it to a file and returns the path to
        the file.

        if a file for the string 'text' exists, that will be used instead of generating
        a new file, unless use_cache=False is set

        """

        fname = self._make_fname(text)
        audiofile_path = os.path.join(self.audio_dir, fname)

        if use_cache and os.path.exists(audiofile_path):
            from_cache = True
            # update access time
            os.utime(audiofile_path)
            logger.debug(f"cached: '{fname}'")

        else:
            from_cache = False
            # generate the audio
            audio = self.tts_generate_audio(text)
            with open(audiofile_path, 'wb') as f:
                soundfile.write(f, audio, self.sample_rate_khz, format=self.audio_format)

            logger.debug(f"wrote file: '{fname}'")

        audiofile_timestamp = os.stat(audiofile_path).st_ctime
        return GLaDOSTTSAudioModel(
            from_cache=from_cache,
            text=text,
            audiofile_name=fname,
            audiofile_timestamp=audiofile_timestamp
        )



    def say(self, text, use_cache=True):
        """shorthand function for Text-to-Speech.

        """

        if not len(text) > 0:
            raise GLaDOSInputError("input must not be empty")

        logger.info(f"input: '{text}'")

        return self.tts_audio_to_file(text, use_cache=use_cache)
