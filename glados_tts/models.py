import os.path
import mimetypes

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field, root_validator


class GLaDOSRequest(BaseModel):
    text: str = Field(description="Text for GLaDOS TTS Engine")
    use_cache: bool = Field(
        True,
        description="Allows retrieving a previously generated audio file for the same text"
    )
    audio_format: str = Field("wav", description="Format that the resulting audio will be encoded in")


mary_compat = "provided for compatability, has no meaning"
class MaryRequest(BaseModel):
    INPUT_TEXT: str = Field(description="Text for GLaDOS TTS", title="input text")
    OUTPUT_TYPE: Literal['AUDIO'] = Field("AUDIO", description=mary_compat)
    INPUT_TYPE: Literal['TEXT'] = Field("TEXT", description=mary_compat)
    LOCALE: Literal['en-GB'] = Field("en-GB", description=mary_compat)
    AUDIO: Literal['WAVE_FILE'] = Field("WAVE_FILE", description=mary_compat)
    VOICE: Literal['GLaDOS'] = Field("GLaDOS", description=mary_compat)


class GLaDOSResponse(BaseModel):
    from_cache: bool = Field(
        title="is returned file is from cache",
        description="wether a previously generated file was returned or not"
    )
    text: str = Field(description="The `text` the GLaDOS TTS engine was asked to speak")
    audio_format: str = Field(description="The format the audio is encoded with")
    audio_filename: str = Field(description="the filename of the TTS audio file")
    audio_timestamp: datetime = Field(description="the timestamp for when the file was created")
    audio_mimetype: str = Field(
        mimetypes.types_map['.wav'],
        description="The MIME type of the file"
    )

    @root_validator
    def get_mimetype(cls, values):
        audio_filename = values.get("audio_filename")
        extension = os.path.splitext(audio_filename)[1]
        values['audio_mimetype'] = mimetypes.types_map.get(extension)
        return values


class HealthResponse(BaseModel):
    status: Literal['healthy', 'unhealthy'] = Field(
        description="GLaDOS API status"
    )
