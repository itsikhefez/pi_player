import argparse
import logging
import os
import sys
import asyncio
import yaml

# import aioconsole
# import tty

from pathlib import Path
from control import Control
from display import DisplayControl
from remote import RemoteControl
from squeezebox import SqueezeboxControl

# TODO:
# [] display integration
# [] volume
# [] streamer mode:
#    [] song artist/title
#    [] album art
# [] change input/mode -- TV/streamer/phono/cassette/Karaoke
# [] remote control
# [] rotary encoder for volume


# async def echo():
#     tty.setraw(sys.stdin.fileno())
#     stdin, _ = await aioconsole.stream.get_standard_streams()
#     while True:
#         ch = await stdin.read(1)
#         if ch == b"\x03":  # ctrl-c
#             loop.stop()


async def main():
    os.system("clear")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log",
        default="WARNING",
        help="sets logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.log)

    cwd = Path(__file__).resolve().parent
    config_path = cwd.joinpath("config.yaml")
    config = yaml.safe_load(config_path.read_text())

    displayctl = DisplayControl(config["display"], cwd)
    ctl = Control(displayctl=displayctl)
    remotectl = RemoteControl(ctl=ctl, displayctl=displayctl)
    squeezectl = SqueezeboxControl(displayctl=displayctl)
    await asyncio.gather(
        squeezectl.loop(),
        remotectl.loop(),
    )
    displayctl.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(main()))
