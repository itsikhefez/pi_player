import argparse
import logging
import os
import sys

from control import Control
from squeezebox import squeezebox_loop
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

    control = Control()
    await asyncio.gather(
        squeezebox_loop(),
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(main()))
