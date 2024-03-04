import logging
import urllib.request
from typing import List
from pathlib import Path
from display import DisplayControl
from PIL import ImageFont


RESOURCES_PATH = Path(__file__).resolve().parent.joinpath("resources")


class DisplayMode:
    async def render(self, displayctl: DisplayControl):
        pass


class DefaultDisplayMode(DisplayMode):
    def __init__(self):
        pass

    async def render(self, displayctl: DisplayControl):
        pass


class MediaPlayerDisplayMode(DisplayMode):
    def __init__(self):
        pass

    async def render(self, displayctl: DisplayControl):
        pass


class VolumeDisplayMode(DisplayMode):
    font_path = str(RESOURCES_PATH.joinpath("Hack-Regular.ttf"))
    default_font = ImageFont.truetype(font_path, 48)

    def __init__(self, volume: float):
        self.volume = volume

    async def render(self, displayctl: DisplayControl):
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

    def __init__(self, url):
        self.url = url

    async def render(self, displayctl: DisplayControl):
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

    async def render(self, displayctl: DisplayControl):
        displayctl.show_image(path=self.image_gallery[self.gallery_index], stretch=True)

    def scroll_gallery(self) -> DisplayMode:
        self.gallery_index = (self.gallery_index + 1) % len(self.image_gallery)
        return self