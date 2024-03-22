from PIL import Image, ImageOps
from luma.core.render import canvas
from luma.core.interface.serial import spi
from luma.oled.device import ssd1351


class DisplayControl:
    def __init__(self):
        serial = spi(
            gpio_DC=23,
            gpio_RST=24,
            bus_speed_hz=16000000,
        )
        self.device = ssd1351(serial_interface=serial, bgr=True)
        self.device.contrast(128)

    def close(self):
        self.device.cleanup()

    def clear(self):
        self.device.clear()

    def display_size(self):
        return self.device.size

    def show_image(self, path: str, stretch=False) -> None:
        image = Image.open(path, formats=["JPEG", "PNG"]).convert("RGB")

        if not stretch:
            image = ImageOps.pad(
                ImageOps.contain(image, self.display_size()), self.display_size()
            )
        else:
            image = image.resize(self.display_size())

        self.device.display(image)
        image.close()

    def get_canvas(self) -> canvas:
        return canvas(self.device)
