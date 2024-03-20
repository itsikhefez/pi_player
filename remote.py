import evdev
import logging

from enum import Enum, auto
from control import Control, InputMode
from media_player import MediaPlayerControl, MediaPlayerOp
from throttle import Debounce, TokenBucket

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
    HOLD_PREV = auto()
    NEXT = auto()
    HOLD_NEXT = auto()
    MEGA_XPAND = auto()
    MEGA_BASS = auto()


INPUT_DEVICE = "/dev/input/event0"
KEYMAP = {
    0x440047: RemoteButton.FUNCTION,
    0x440060: RemoteButton.SLEEP,
    0x440015: RemoteButton.POWER,
    0x640000: RemoteButton.ONE,
    0x640001: RemoteButton.TWO,
    0x640002: RemoteButton.THREE,
    0x640003: RemoteButton.FOUR,
    0x640004: RemoteButton.FIVE,
    0x640005: RemoteButton.SIX,
    0x640006: RemoteButton.SEVEN,
    0x640007: RemoteButton.EIGHT,
    0x640008: RemoteButton.NINE,
    0x440011: RemoteButton.MODE,
    0x64000C: RemoteButton.ZERO_TEN,
    0x64000D: RemoteButton.GT_TEN,
    0x64006F: RemoteButton.BAND,
    0x640073: RemoteButton.TUNE_UP,
    0x640074: RemoteButton.TUNE_DOWN,
    0x440012: RemoteButton.VOL_UP,
    0x440013: RemoteButton.VOL_DOWN,
    0x640032: RemoteButton.PLAY,
    0x640039: RemoteButton.PAUSE,
    0x640038: RemoteButton.STOP,
    0x640030: RemoteButton.PREV,
    0x64003A: RemoteButton.HOLD_PREV,
    0x640031: RemoteButton.NEXT,
    0x64003B: RemoteButton.HOLD_NEXT,
    0x44002A: RemoteButton.MEGA_XPAND,
    0x44003F: RemoteButton.MEGA_BASS,
}


class RemoteControl:
    def __init__(self, ctl: Control, mediactl: MediaPlayerControl):
        self.button_throttle = Debounce(0.15)
        self.volume_throttle = TokenBucket(1, 0.175)
        self.device = evdev.InputDevice(INPUT_DEVICE)
        self.ctl = ctl
        self.mediactl = mediactl
        logging.info(self.device)

    async def refresh_loop(self):
        logging.info("started remote event listener...")
        async for event in self.device.async_read_loop():
            code = event.value
            button = KEYMAP.get(code)
            if not button:
                continue
            await self.handle_keypress(button)

    def has_tokens(self, button: int) -> bool:
        if button in (
            RemoteButton.VOL_UP,
            RemoteButton.VOL_DOWN,
            RemoteButton.TUNE_UP,
            RemoteButton.TUNE_DOWN,
        ):
            return self.volume_throttle.has_tokens()
        else:
            return self.button_throttle.has_tokens()

    async def handle_keypress(self, button: int, force: bool = False) -> None:
        if not force and not self.has_tokens(button):
            return
        logging.info("handle_keypress. %s", button)
        match button:
            case RemoteButton.FUNCTION:
                print("FUNCTION")
            case RemoteButton.SLEEP:
                print("SLEEP")
            case RemoteButton.POWER:
                await self.ctl.set_display_mode(self.ctl.image_gallery.scroll_gallery())
            case RemoteButton.ONE:
                await self.ctl.change_input(0)
            case RemoteButton.TWO:
                await self.ctl.change_input(1)
            case RemoteButton.THREE:
                await self.ctl.change_input(2)
            case RemoteButton.FOUR:
                await self.ctl.change_input(3)
            case RemoteButton.FIVE:
                await self.ctl.change_input(4)
            case RemoteButton.SIX:
                print("SIX")
            case RemoteButton.SEVEN:
                print("SEVEN")
            case RemoteButton.EIGHT:
                print("EIGHT")
            case RemoteButton.NINE:
                print("NINE")
            case RemoteButton.MODE:
                print("MODE")
            case RemoteButton.ZERO_TEN:
                print("0/10")
            case RemoteButton.GT_TEN:
                await self.ctl.next_input()
            case RemoteButton.BAND:
                await self.ctl.volume_dim()
            case RemoteButton.TUNE_UP:
                await self.ctl.volume_step(0.5)
            case RemoteButton.TUNE_DOWN:
                await self.ctl.volume_step(-0.5)
            case RemoteButton.VOL_UP:
                await self.ctl.volume_step(3.0)
            case RemoteButton.VOL_DOWN:
                await self.ctl.volume_step(-3.0)
            case RemoteButton.PLAY:
                await self.mediactl.op(MediaPlayerOp.PLAY)
            case RemoteButton.PAUSE:
                await self.mediactl.op(MediaPlayerOp.PAUSE)
            case RemoteButton.STOP:
                await self.mediactl.op(MediaPlayerOp.STOP)
            case RemoteButton.PREV:
                await self.mediactl.op(MediaPlayerOp.PREV)
            case RemoteButton.HOLD_PREV:
                print("HOLD_PREV")
            case RemoteButton.NEXT:
                await self.mediactl.op(MediaPlayerOp.NEXT)
            case RemoteButton.HOLD_NEXT:
                print("HOLD_NEXT")
            case RemoteButton.MEGA_XPAND:
                await self.ctl.change_input_mode(mode=InputMode.EQ_ALT)
            case RemoteButton.MEGA_BASS:
                await self.ctl.change_input_mode(mode=InputMode.EQ)
            case _:
                raise Exception(f"{button} not assigned")
