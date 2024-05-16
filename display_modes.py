import asyncio
import logging
import urllib.request
from typing import List
from pathlib import Path
from control_state import ControlState, InputMode
from display import DisplayControl, DisplayType
from song_state import SongState
from PIL import ImageFont


RESOURCES_PATH = Path(__file__).resolve().parent.joinpath("resources")


class DisplayMode:
    def render(self, displayctl: DisplayControl):
        pass


class MediaPlayerDisplayMode(DisplayMode):
    font_path = str(RESOURCES_PATH.joinpath("Hack-Regular.ttf"))
    default_font = ImageFont.truetype(font_path, 26)

    def __init__(self, song_state: SongState, volume=None):
        self.song_state = song_state
        self.volume = volume

    def render(self, displayctl: DisplayControl):
        def fit(s):
            CHARS = 15
            if len(s) <= CHARS:
                return s
            return f"{s:.15}"

        s = self.song_state
        samplerate = f"{float(s.samplerate)/1000}k" if s.samplerate else ""
        # fmt: off
        text = (
            f"{s.artist:.15}\n"
            f"{fit(s.title)}\n"
            f"{fit(s.album)}\n"
        )
        # fmt: on
        with displayctl.get_canvas() as draw:
            draw.text(
                (0, 0),
                text,
                font=MediaPlayerDisplayMode.default_font,
                fill="white",
                align="left",
            )
            draw.text(
                (240 - len(samplerate) * 16, 208),
                samplerate,
                font=MediaPlayerDisplayMode.default_font,
                fill="green",
                align="right",
            )
            if self.volume:
                volume_str = f"{self.volume:5}dB"
                draw.text(
                    (0, 108),
                    volume_str,
                    font=MediaPlayerDisplayMode.default_font,
                    fill="purple",
                    align="right",
                )


class VolumeDisplayMode(DisplayMode):
    font_path = str(RESOURCES_PATH.joinpath("Hack-Regular.ttf"))
    vol_font = ImageFont.truetype(font_path, 96)
    db_font = ImageFont.truetype(font_path, 72)

    def __init__(self, volume: float):
        if volume > -10.0:
            self.volume = str(volume)
        else:
            self.volume = f"{int(volume)}{'' if volume.is_integer() else '.'}"

    def render(self, displayctl: DisplayControl):
        with displayctl.get_canvas() as draw:
            draw.text(
                (0, 5),
                f"{self.volume}",
                font=VolumeDisplayMode.vol_font,
                fill="white",
            )
            draw.text(
                (120, 120),
                f"dB",
                font=VolumeDisplayMode.db_font,
                fill="white",
            )


class AlbumArtDisplayMode(DisplayMode):
    default_image = str(RESOURCES_PATH.joinpath("default_album_art.png"))

    def __init__(self, song_state: SongState):
        self.url = song_state.image_url

    def render(self, displayctl: DisplayControl):
        try:
            img_tmp_path = "/tmp/img-tmp"
            urllib.request.urlretrieve(self.url, img_tmp_path)
            displayctl.show_image(path=img_tmp_path)
        except Exception as e:
            logging.error("%s, %s", e, img_tmp_path)
            displayctl.show_image(path=AlbumArtDisplayMode.default_image)


class ImageGalleryDisplayMode(DisplayMode):
    def __init__(self, cwd: Path, images: List[str]):
        self.image_gallery = [cwd.joinpath("resources", f) for f in images]
        self.gallery_index = 0

    def render(self, displayctl: DisplayControl):
        displayctl.show_image(path=self.image_gallery[self.gallery_index], stretch=True)

    def scroll_gallery(self) -> DisplayMode:
        self.gallery_index = (self.gallery_index + 1) % len(self.image_gallery)
        return self


class InputDisplayMode(DisplayMode):
    font_path = str(RESOURCES_PATH.joinpath("Hack-Regular.ttf"))
    input_font = ImageFont.truetype(font_path, 54)

    def __init__(self, state: ControlState):
        self.state = state

    def render(self, displayctl: DisplayControl):
        with displayctl.get_canvas() as draw:
            draw.text(
                (0, 20),
                f"{self.state.input.name}",
                font=InputDisplayMode.input_font,
                fill="white",
            )
            outline_width = 5
            left = 170
            bottom = 230
            match self.state.input_mode:
                case InputMode.EQ:
                    draw.ellipse(
                        (left, bottom - 60, left + 60, bottom),
                        fill="blue",
                        outline="magenta",
                        width=outline_width,
                    )
                case InputMode.EQ_ALT:
                    draw.polygon(
                        (left, bottom, left + 60, bottom, left + 30, bottom - 60),
                        fill="red",
                        outline="brown",
                        width=outline_width,
                    )
                case _:
                    draw.rectangle(
                        (left, bottom - 60, left + 60, bottom),
                        fill="green",
                        outline="cyan",
                        width=outline_width,
                    )


class DisplayQueue:
    def __init__(self, displayctl: DisplayControl):
        self.displayctl = displayctl
        self.q = asyncio.Queue()

    def put(self, mode: DisplayMode):
        self.q.put_nowait(mode)

    async def refresh_loop(self):
        while True:
            try:
                async with asyncio.timeout(600):
                    mode = await self.q.get()
                    while not self.q.empty():
                        mode = await self.q.get()

                    assert isinstance(mode, DisplayMode)
                    mode.render(self.displayctl)
                    self.q.task_done()
            except TimeoutError:
                self.displayctl.clear()


class DisplayManager:
    def __init__(self):
        self.queue = DisplayQueue(DisplayControl(type=DisplayType.LCD))
        self.modes = [AlbumArtDisplayMode, MediaPlayerDisplayMode]
        self.current_index = 0
        self.song_state = None
        self.pending_revert = None

    def new_display_mode(self) -> DisplayMode:
        return self.modes[self.current_index](self.song_state)

    def update_song_state(self, song_state: SongState):
        self.song_state = song_state
        self.queue.put(self.new_display_mode())

    def scroll_display_mode(self):
        self.current_index = (self.current_index + 1) % len(self.modes)
        self.queue.put(self.new_display_mode())

    def put_temp(self, mode: DisplayMode):
        if self.pending_revert:
            self.pending_revert.cancel()

        self.queue.put(mode)
        self.pending_revert = asyncio.create_task(coro=self.revert_display_after(2))

    async def revert_display_after(self, delay: int):
        await asyncio.sleep(delay)
        self.queue.put(self.new_display_mode())
