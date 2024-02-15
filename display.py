import logging
import urllib.request

from PIL import Image, ImageOps, ImageFont
from luma.core.render import canvas
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from pathlib import Path


class DisplayControl:
    def __init__(self):
        serial = spi(
            gpio_DC=23,
            gpio_RST=24,
            bus_speed_hz=32000000,
            reset_hold_time=0.1,
            reset_release_time=0.1,
        )
        self.device = st7735(
            serial_interface=serial, width=160, height=128, active_low=False, rotate=2
        )
        font_path = str(
            Path(__file__).resolve().parent.joinpath("resources", "Hack-Regular.ttf")
        )
        self.font = ImageFont.truetype(font_path, 48)

    def close(self):
        self.device.cleanup()

    def display_size(self):
        return self.device.size

    def album_art(self, url: str):
        try:
            img_tmp_path = "img-tmp"
            urllib.request.urlretrieve(url, img_tmp_path)
            image = Image.open(img_tmp_path, formats=["JPEG"])
            image = ImageOps.pad(
                ImageOps.contain(image, self.display_size()), self.display_size()
            )
            self.device.display(image)
            image.close()
        except Exception as e:
            logging.error("%s, %s", e, url)

    def show_volume(self, volume: float):
        with canvas(self.device) as draw:
            draw.text(
                (0, 0), f"{volume}\ndB", font=self.font, fill="green", align="right"
            )
