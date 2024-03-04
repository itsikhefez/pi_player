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
# [] streamer mode:
#    [] song artist/title
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

    cwd = Path(__file__).resolve().parent
    config_path = cwd.joinpath("config.yaml")
    config = yaml.safe_load(config_path.read_text())

    displayctl = DisplayControl(cwd)
    ctl = Control(cwd, config, displayctl)
    squeezectl = SqueezeboxControl(config["squeezebox"], ctl)
    remotectl = RemoteControl(ctl, mediactl=squeezectl)
    await asyncio.gather(
        squeezectl.loop(),
        remotectl.loop(),
    )
    displayctl.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(main()))
