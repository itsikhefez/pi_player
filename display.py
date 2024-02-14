import urllib.request
from PIL import Image, ImageOps

from luma.core import cmdline, error

# --display=st7735
# --interface=spi
# --spi-bus-speed=32000000
# --gpio-reset=24
# --gpio-data-command=23
# --gpio-backlight=18
# --width=160
# --height=128
# --backlight-active=high
# --gpio-reset-hold-time=0.1
# --gpio-reset-release-time=0.1


def get_device():
    parser = cmdline.create_parser(description="luma.examples arguments")
    config = cmdline.load_config("/home/itsik/src/pi_player/st7735.conf")
    args = parser.parse_args(config)
    try:
        device = cmdline.create_device(args)
        print(display_settings(device, args))
        return device

    except error.Error as e:
        parser.error(e)
        return None


def display_settings(device, args):
    """
    Display a short summary of the settings.

    :rtype: str
    """
    iface = ""
    display_types = cmdline.get_display_types()
    if args.display not in display_types["emulator"]:
        iface = f"Interface: {args.interface}\n"

    lib_name = cmdline.get_library_for_display_type(args.display)
    if lib_name is not None:
        lib_version = cmdline.get_library_version(lib_name)
    else:
        lib_name = lib_version = "unknown"

    import luma.core

    version = f"luma.{lib_name} {lib_version} (luma.core {luma.core.__version__})"

    return f'Version: {version}\nDisplay: {args.display}\n{iface}Dimensions: {device.width} x {device.height}\n{"-" * 60}'


DISPLAY_SIZE = (160, 128)

device = get_device()

def image(url: str):
    urllib.request.urlretrieve(url, "img-tmp")
    # img_path = str(Path(__file__).resolve().parent.joinpath("images", "pi_logo.png"))
    img_path = "img-tmp"
    image = Image.open(img_path, formats=["JPEG"]).rotate(180)
    image = ImageOps.pad(ImageOps.contain(image, DISPLAY_SIZE), DISPLAY_SIZE)
    device.display(image)
    image.close()
