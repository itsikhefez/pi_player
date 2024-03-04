from enum import Enum, auto


class MediaPlayerOp(Enum):
    PREV = auto()
    NEXT = auto()
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()


class MediaPlayerControl:
    async def op(self, op: MediaPlayerOp) -> None:
        pass
