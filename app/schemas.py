from typing import Literal
from pydantic import BaseModel,Field,HttpUrl
class ProjectCreate(BaseModel):
 topic:str=Field(min_length=5,max_length=500)
 title:str|None=Field(default=None,max_length=160)
 mode:Literal["topic","competitor"]="topic"
 competitor_url:HttpUrl|None=None
 target_format:Literal["long","short","both"]="long"
 target_minutes:int=Field(default=5,ge=1,le=60)
 language:str=Field(default="English",min_length=2,max_length=40)
 audience:str=Field(default="general audience",max_length=160)
 tone:str=Field(default="engaging, clear, factual",max_length=160)
class RenderRequest(BaseModel):
 image_paths:list[str]=Field(min_length=1,max_length=100)
 audio_path:str|None=None
 output_name:str=Field(default="video.mp4",pattern=r"^[a-zA-Z0-9_.-]+$")
 width:int=Field(default=1920,ge=320,le=3840)
 height:int=Field(default=1080,ge=320,le=2160)
 fps:int=Field(default=30,ge=1,le=60)
class VoiceRequest(BaseModel):
 text:str=Field(min_length=1,max_length=8000)
 filename:str=Field(default="voice.wav",pattern=r"^[a-zA-Z0-9_.-]+$")
class MediaSearchRequest(BaseModel):
 query:str=Field(min_length=2,max_length=120)
 per_page:int=Field(default=12,ge=1,le=30)
class ThumbnailRequest(BaseModel):
 title:str=Field(min_length=2,max_length=120)
 background_path:str|None=None
 filename:str=Field(default="thumbnail.jpg",pattern=r"^[a-zA-Z0-9_.-]+$")
