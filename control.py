import logging
from typing import List
from camilladsp import CamillaClient
from control_state import ControlState, Input, InputMode
from display_modes import (
    VolumeDisplayMode,
    DisplayManager,
    InputDisplayMode,
    AlbumArtDisplayMode,
)
from song_state import SongState


MIN_VOLUME: float = -80.0
MAX_VOLUME: float = 0.0
DIM_STEP: float = 20.0


class ControlConfig:
    def __init__(self, config: dict):
        self.cdsp_configs_path = config["camilladsp_configs_path"]
        self.inputs: List[Input] = []
        index = 0
        for k, v in config["inputs"].items():
            self.inputs.append(Input(index=index, name=k, configs=v))
            index += 1
        assert len(self.inputs) > 0, "must have atleast 1 input in config"


class Control:
    def __init__(
        self,
        config: dict,
    ):
        self.display_manager = DisplayManager()
        self.config = ControlConfig(config)

        self.cdsp_client = CamillaClient("127.0.0.1", 1234)
        self.cdsp_client.connect()
        cdsp_config_path = self.cdsp_client.config.file_path().removeprefix(
            self.config.cdsp_configs_path
        )
        current_input = None
        for input in self.config.inputs:
            for j, filepath in enumerate(input.configs):
                if cdsp_config_path == filepath:
                    current_input = input
                    input_mode = InputMode(j)
                    break

        assert current_input is not None, f"invalid input file {cdsp_config_path}"

        self.state = ControlState(current_input, input_mode)
        self.display_manager.put(InputDisplayMode(self.state))
        self.cdsp_client.volume.set_main(self.state.volume)
        self.song_state: SongState | None = None
        logging.info("cdsp connected. %s", self.state)

    async def change_input_mode(self, mode: InputMode) -> None:
        self.state.input_mode = (
            InputMode.DIRECT if (self.state.input_mode == mode) else mode
        )
        await self.apply_input_state()

    async def change_input(self, i: int) -> None:
        assert i >= 0 and i < len(self.config.inputs)
        self.state.input = self.config.inputs[i]
        await self.apply_input_state()

    async def next_input(self, prev: bool = False) -> None:
        index = (self.state.input.index - (1 if prev else -1)) % len(self.config.inputs)
        self.state.input = self.config.inputs[index]
        await self.apply_input_state()

    async def apply_input_state(self):
        path = f"{self.config.cdsp_configs_path}{self.state.input.configs[self.state.input_mode.value]}"
        logging.info("apply_input_state. %s. %s", self.state, path)
        self.cdsp_client.config.set_file_path(path)
        self.cdsp_client.general.reload()
        if self.state.input.name == "Digital" and self.song_state:
            self.display_manager.put(AlbumArtDisplayMode(self.song_state))
        else:
            self.display_manager.put(InputDisplayMode(self.state))

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
        self.display_manager.put_temp(VolumeDisplayMode(self.state.volume))

    async def volume_dim(self) -> None:
        self.state.dim = -1 * self.state.dim
        volume_step = self.state.dim * DIM_STEP
        logging.info("volume_dim. %d", self.state.dim)
        await self.volume_step(volume_step=volume_step, reset_dim=False)

    async def mute(self) -> None:
        return None

    async def update_song_state(self, song_state: SongState) -> None:
        logging.info("update_song_state. %s", song_state)
        self.song_state = song_state

        if self.state.input.name == "Digital":
            self.display_manager.put(AlbumArtDisplayMode(song_state))
