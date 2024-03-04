import asyncio
import logging

from pathlib import Path
from typing import Dict, List
from enum import Enum, auto
from camilladsp import CamillaClient, CamillaError
from display import DisplayControl
from display_modes import (
    DisplayMode,
    AlbumArtDisplayMode,
    ImageGalleryDisplayMode,
    VolumeDisplayMode,
)

# TODO:
# [] display integration
# [] volume
# [] streamer mode:
#    [] song artist/title
#    [] album art
# [] change input/mode -- TV/streamer/phono/cassette/Karaoke

# [] remote control
# rotary encoder for volume


class InputMode(Enum):
    DIRECT = 0
    EQ = 1
    EQ_ALT = 2


class Input:
    name: str
    configs: List[str]

    def __init__(self, name, configs):
        self.name = name
        self.configs = configs


INPUTS = [
    # configs for DIRECT, EQ, EQ_ALT
    Input(
        name="TV",
        configs=[
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_toslink_48c_48p.yaml",
        ],
    ),
    Input(
        name="Phono",
        configs=[
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_analog_48c_48p.yaml",
            "ucx2_toslink_48c_48p.yaml",
        ],
    ),
    Input(
        name="Tape",
        configs=[
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_analog_48c_48p.yaml",
            "ucx2_toslink_48c_48p.yaml",
        ],
    ),
    Input(
        name="Digital",
        configs=[
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_streamer_44c_44p_MP.yaml",
            "ucx2_toslink_48c_48p.yaml",
        ],
    ),
    Input(
        name="Karaoke",
        configs=[
            "ucx2_toslink_48c_48p.yaml",
            "ucx2_streamer_44c_44p_MP.yaml",
            "ucx2_toslink_48c_48p.yaml",
        ],
    ),
]

CAMILLADSP_CONFIGS_PATH = "/home/itsik/camilladsp/configs/"
MIN_VOLUME: float = -80.0
MAX_VOLUME: float = 0.0
DIM_STEP: float = 20.0


class SongState:
    def __init__(
        self,
        album: str = None,
        artist: str = None,
        title: str = None,
        elapsed: int = 0,
        length: int = 0,
        bitrate: int = 0,
        format: str = None,
        image_url: str = None,
    ):
        self.album = album
        self.artist = artist
        self.song = title
        self.elapsed = elapsed
        self.length = length
        self.bitrate = bitrate
        self.format = format
        self.image_url = image_url

    def __eq__(self, other) -> bool:
        return (
            self.album == other.album
            and self.artist == other.artist
            and self.song == other.song
        )

    def __str__(self) -> str:
        return f"{self.artist}|{self.album}|{self.song}|{self.bitrate}|{self.format}"


class State:
    def __init__(self, input, input_mode, display_mode=None):
        self.input = input
        self.input_mode = input_mode
        self.volume: float = -40.0
        self.dim: int = 1
        self.display_mode = display_mode

    def __str__(self) -> str:
        return f"input:{INPUTS[self.input].name:>7}, input_mode:{self.input_mode}, vol:{self.volume}, disp:{self.display_mode}"


class Control:
    def __init__(
        self,
        cwd: Path,
        config: dict,
        displayctl: DisplayControl,
    ):
        self.displayctl = displayctl
        self.cdsp_client = CamillaClient("127.0.0.1", 1234)
        self.cdsp_client.connect()
        self.display_mode: DisplayMode = None
        self.pending_display_task = None
        self.image_gallery = ImageGalleryDisplayMode(cwd, config["image_gallery"])

        config_path = self.cdsp_client.config.file_path().removeprefix(
            CAMILLADSP_CONFIGS_PATH
        )
        for i, input in enumerate(INPUTS):
            for j, filepath in enumerate(input.configs):
                if config_path == filepath:
                    current_input = i
                    input_mode = InputMode(j)

        self.state = State(current_input, input_mode)
        self.cdsp_client.volume.set_main(self.state.volume)
        logging.info("cdsp connected. %s", self.state)

    async def change_input_mode(self, mode: InputMode) -> None:
        self.state.input_mode = (
            InputMode.DIRECT if (self.state.input_mode == mode) else mode
        )
        await self.apply_input_state()

    async def change_input(self, input: int) -> None:
        assert input >= 0 and input < len(INPUTS)
        self.state.input = input
        await self.apply_input_state()

    async def next_input(self, prev: bool = False) -> None:
        if prev:
            input = self.state.input - 1
        else:
            input = self.state.input + 1
        self.state.input = input % len(INPUTS)
        await self.apply_input_state()

    async def apply_input_state(self):
        path = f"{CAMILLADSP_CONFIGS_PATH}{INPUTS[self.state.input].configs[self.state.input_mode.value]}"
        logging.info("apply_input_state. %s. %s", self.state, path)
        self.cdsp_client.config.set_file_path(path)
        self.cdsp_client.general.reload()

    async def volume_step(self, volume_step: float, reset_dim: bool = True) -> None:
        if self.pending_display_task:
            self.pending_display_task.cancel()

        if reset_dim:
            self.state.dim = 1
        next_volume = round(self.state.volume + volume_step, 1)
        next_volume = max(MIN_VOLUME, min(MAX_VOLUME, next_volume))
        if next_volume == self.state.volume:
            return

        logging.info("volume_step. %.2fdB", next_volume)
        self.cdsp_client.volume.set_main(next_volume)
        self.state.volume = next_volume
        await VolumeDisplayMode(self.state.volume).render(self.displayctl)

        self.pending_display_task = asyncio.create_task(self.revert_display_mode())

    async def volume_dim(self) -> None:
        self.state.dim = -1 * self.state.dim
        volume_step = self.state.dim * DIM_STEP
        logging.info("volume_dim. %d", self.state.dim)
        await self.volume_step(volume_step=volume_step, reset_dim=False)

    async def mute(self) -> None:
        return None

    async def update_song_state(self, song_state: SongState) -> None:
        logging.info("update_song_state. %s", song_state)
        self.display_mode = AlbumArtDisplayMode(url=song_state.image_url)
        await self.display_mode.render(self.displayctl)

    async def set_display_mode(self, display_mode: DisplayMode) -> None:
        await display_mode.render(self.displayctl)
        self.display_mode = display_mode

    async def revert_display_mode(self):
        try:
            await asyncio.sleep(5)
            await self.display_mode.render(self.displayctl)
        except asyncio.CancelledError:
            pass
