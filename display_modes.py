import asyncio
import logging
import urllib.request
from typing import List
from pathlib import Path
from display import DisplayControl
from song_state import SongState
from PIL import ImageFont


RESOURCES_PATH = Path(__file__).resolve().parent.joinpath("resources")


class DisplayMode:
    def render(self, displayctl: DisplayControl):
        pass


class MediaPlayerDisplayMode(DisplayMode):
    font_path = str(RESOURCES_PATH.joinpath("Hack-Regular.ttf"))
    default_font = ImageFont.truetype(font_path, 16)

    def __init__(self, song_state: SongState, volume=None):
        self.song_state = song_state
        self.volume = volume

    def render(self, displayctl: DisplayControl):
        s = self.song_state
        samplerate = f"{float(s.samplerate)/1000}k" if s.samplerate else ""
        # fmt: off
        text = (
            f"{s.artist:.16}\n"
            f"{s.title:.16}\n"
            f"{s.album:.16}r\n"
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
                (160 - len(samplerate) * 10, 108),
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
    default_font = ImageFont.truetype(font_path, 72)

    def __init__(self, volume: float):
        self.volume = volume

    def render(self, displayctl: DisplayControl):
        with displayctl.get_canvas() as draw:
            draw.text(
                (10, 10),
                f"{self.volume:5}\ndB",
                font=VolumeDisplayMode.default_font,
                fill="white",
                align="right",
            )


class AlbumArtDisplayMode(DisplayMode):
    default_image = str(RESOURCES_PATH.joinpath("default_album_art.png"))

    def __init__(self, song_state: SongState):
        self.url = song_state.image_url

    def render(self, displayctl: DisplayControl):
        try:
            img_tmp_path = "img-tmp"
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


class DisplayQueue:
    def __init__(self, displayctl: DisplayControl):
        self.displayctl = displayctl
        self.q = asyncio.Queue()

    def put(self, mode: DisplayMode):
        self.q.put_nowait(mode)

    async def refresh_loop(self):
        while True:
            mode = await self.q.get()
            while not self.q.empty():
                mode = await self.q.get()

            assert isinstance(mode, DisplayMode)
            mode.render(self.displayctl)
            self.q.task_done()


class DisplayManager:
    def __init__(self):
        self.queue = DisplayQueue(DisplayControl())
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
