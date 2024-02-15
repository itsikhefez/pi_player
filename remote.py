import evdev
import logging

from enum import Enum, auto
from control import Control

"""
Remote control functionality
3) Volume inc/dec -- coarse (1.5dB) and fine (0.5dB)
4) Mute/dim
1) Direct input select

2) Input prev/next
5) Display toggle -- album art/song info/volume/system (capture rate, playback rate, etc)
6) EQ on/off
7) Next/prev song
8) Play/pause
"""


class RemoteButton(Enum):
    FUNCTION = auto()
    SLEEP = auto()
    POWER = auto()
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()
    SIX = auto()
    SEVEN = auto()
    EIGHT = auto()
    NINE = auto()
    MODE = auto()
    ZERO_TEN = auto()
    GT_TEN = auto()
    BAND = auto()
    TUNE_UP = auto()
    TUNE_DOWN = auto()
    VOL_UP = auto()
    VOL_DOWN = auto()
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()
    PREV = auto()
    NEXT = auto()
    MEGA_XPAND = auto()
    MEGA_BASS = auto()


INPUT_DEVICE = "/dev/input/event0"
KEYMAP = {
    0x1F000: RemoteButton.FUNCTION,
    0x1F000: RemoteButton.SLEEP,
    0x10015: RemoteButton.POWER,
    0x10000: RemoteButton.ONE,
    0x10001: RemoteButton.TWO,
    0x10002: RemoteButton.THREE,
    0x10003: RemoteButton.FOUR,
    0x10004: RemoteButton.FIVE,
    0x10005: RemoteButton.SIX,
    0x10006: RemoteButton.SEVEN,
    0x10007: RemoteButton.EIGHT,
    0x10008: RemoteButton.NINE,
    0x1F000: RemoteButton.MODE,
    0x1F000: RemoteButton.ZERO_TEN,
    0x1F000: RemoteButton.GT_TEN,
    0x1F000: RemoteButton.BAND,
    0x1F000: RemoteButton.TUNE_UP,
    0x1F000: RemoteButton.TUNE_DOWN,
    0x10012: RemoteButton.VOL_UP,
    0x10013: RemoteButton.VOL_DOWN,
    0x1F000: RemoteButton.PLAY,
    0x1F000: RemoteButton.PAUSE,
    0x1F000: RemoteButton.STOP,
    0x1F000: RemoteButton.PREV,
    0x1F000: RemoteButton.NEXT,
    0x1F000: RemoteButton.MEGA_XPAND,
    0x1F000: RemoteButton.MEGA_BASS,
}


class RemoteControl:
    device: evdev.InputDevice

    def __init__(self, ctl: Control):
        self.device = evdev.InputDevice(INPUT_DEVICE)
        self.ctl = ctl
        logging.info(self.device)

    async def loop(self):
        logging.info("started remote event listener...")
        async for event in self.device.async_read_loop():
            code = event.value
            button = KEYMAP.get(code)
            if code == 0x0 or code > 0x5F000000:
                continue
            if not button:
                logging.info("unrecognized remote button %s", hex(code))
                continue

            match button:
                case RemoteButton.VOL_UP:
                    await self.ctl.volume_step(0.5)
                case RemoteButton.VOL_DOWN:
                    await self.ctl.volume_step(-0.5)
                case _:
                    print(f"{button} not assigned to any function")
