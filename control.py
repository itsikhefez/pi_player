import asyncio
import logging
import throttler

from typing import Dict, List
from enum import Enum
from camilladsp import CamillaClient, CamillaError
from display import DisplayControl

# TODO:
# [] display integration
# [] volume
# [] streamer mode:
#    [] song artist/title
#    [] album art
# [] change input/mode -- TV/streamer/phono/cassette/Karaoke

# [] remote control
# rotary encoder for volume


class InputMode:
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
    Input(name="TV", configs=["", "ucx2_toslink_48c_48p.yaml", ""]),
    Input(name="Phono", configs=["", "ucx2_analog_48c_48p.yaml", ""]),
    Input(name="Tape", configs=["", "ucx2_analog_48c_48p.yaml", ""]),
    Input(name="Digital", configs=["", "ucx2_streamer_44c_44p_MP.yaml", ""]),
]

CAMILLADSP_CONFIGS_PATH = "/home/itsik/camilladsp/configs/"
MIN_VOLUME: float = -50.0
MAX_VOLUME: float = 0.0
DIM_STEP: float = 20.0


class Control:
    def __init__(self, displayctl: DisplayControl):
        self.displayctl = displayctl
        self.cdsp_client = CamillaClient("127.0.0.1", 1234)
        self.cdsp_client.connect()

        config_path = self.cdsp_client.config.file_path().removeprefix(
            CAMILLADSP_CONFIGS_PATH
        )
        for i, input in enumerate(INPUTS):
            for j, filepath in enumerate(input.configs):
                if config_path == filepath:
                    self.input = i
                    self.input_mode = j
        self.volume: float = -40.0
        self.dim: int = 1
        self.cdsp_client.volume.set_main(self.volume)
        logging.info(
            "cdsp connected. input: %d, mode: %d, volume: %f",
            self.input,
            self.input_mode,
            self.volume,
        )

    async def change_input(self, prev: bool = False) -> None:
        if prev:
            self.input = self.input - 1
        else:
            self.input = self.input + 1
        self.input = self.input % len(INPUTS)
        path = f"{CAMILLADSP_CONFIGS_PATH}{INPUTS[self.input].configs[self.input_mode]}"

        logging.info("change_input to %s, path %s", self.input, path)
        self.cdsp_client.config.set_file_path(path)
        self.cdsp_client.general.reload()

    async def volume_step(self, volume_step: float) -> None:
        next_volume = round(self.volume + volume_step, 1)
        next_volume = max(MIN_VOLUME, min(MAX_VOLUME, next_volume))
        if next_volume == self.volume:
            return

        logging.info("volume_step. set volume to = %f", next_volume)
        self.cdsp_client.volume.set_main(next_volume)
        self.volume = next_volume

        self.displayctl.show_volume(self.volume)

    async def volume_dim(self) -> None:
        self.dim = -1 * self.dim
        volume_step = self.dim * DIM_STEP
        logging.info("volume_dim. volume step = %f", volume_step)
        await self.change_volume(volume_step=volume_step)

    async def mute(self) -> None:
        return None
