import argparse
import logging
import os
import sys

from control import Control
from remote import RemoteControl
from squeezebox import SqueezeboxControl
from display import image
import asyncio

# TODO:
# [] display integration
# [] volume
# [] streamer mode:
#    [] song artist/title
#    [] album art
# [] change input/mode -- TV/streamer/phono/cassette/Karaoke
# [] remote control
# [] rotary encoder for volume


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

    ctl = Control()
    remotectl = RemoteControl()
    squeezectl = SqueezeboxControl()
    await asyncio.gather(
        squeezectl.loop(),
        remotectl.loop(),
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(main()))
