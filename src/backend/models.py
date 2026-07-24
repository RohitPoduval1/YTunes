from dataclasses import dataclass
from typing import List


@dataclass
class Tag:
    id: int
    name: str

@dataclass
class Song:
    id: str
    name: str
    tags: List[Tag]
    url: str

@dataclass
class Playlist:
    id: str
    name: str
