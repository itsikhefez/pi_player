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
    MediaPlayerDisplayMode,
    VolumeDisplayMode,
)
from song_state import SongState

# TODO:
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

MIN_VOLUME: float = -80.0
MAX_VOLUME: float = 0.0
DIM_STEP: float = 20.0


class ControlState:
    def __init__(self, input, input_mode, display_mode=None):
        self.input = input
        self.input_mode = input_mode
        self.volume: float = -40.0
        self.dim: int = 1
        self.display_mode = display_mode

    def __str__(self) -> str:
        return f"input:{INPUTS[self.input].name:>7}, input_mode:{self.input_mode}, vol:{self.volume}, disp:{self.display_mode}"


class ControlConfig:
    def __init__(self, config: dict):
        self.cdsp_configs_path = config["camilladsp_configs_path"]


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
        self.image_gallery = ImageGalleryDisplayMode(cwd, config["image_gallery"])
        self.config = ControlConfig(config)

        config_path = self.cdsp_client.config.file_path().removeprefix(
            self.config.cdsp_configs_path
        )
        current_input = -1
        for i, input in enumerate(INPUTS):
            for j, filepath in enumerate(input.configs):
                if config_path == filepath:
                    current_input = i
                    input_mode = InputMode(j)

        assert current_input > 0, f"invalid input file {config_path}"

        self.state = ControlState(current_input, input_mode)
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
        path = f"{self.config.cdsp_configs_path}{INPUTS[self.state.input].configs[self.state.input_mode.value]}"
        logging.info("apply_input_state. %s. %s", self.state, path)
        self.cdsp_client.config.set_file_path(path)
        self.cdsp_client.general.reload()

    async def volume_step(self, volume_step: float, reset_dim: bool = True) -> None:
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

    async def volume_dim(self) -> None:
        self.state.dim = -1 * self.state.dim
        volume_step = self.state.dim * DIM_STEP
        logging.info("volume_dim. %d", self.state.dim)
        await self.volume_step(volume_step=volume_step, reset_dim=False)

    async def mute(self) -> None:
        return None

    async def update_song_state(self, song_state: SongState) -> None:
        logging.info("update_song_state. %s", song_state)
        # self.display_mode = AlbumArtDisplayMode(url=song_state.image_url)
        self.display_mode = MediaPlayerDisplayMode(song_state)
        await self.display_mode.render(self.displayctl)

    async def set_display_mode(self, display_mode: DisplayMode) -> None:
        await display_mode.render(self.displayctl)
        self.display_mode = display_mode
