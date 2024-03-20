import argparse
import logging
import sys
import asyncio
import yaml

from pathlib import Path
from control import Control
from display import DisplayControl
from display_modes import DisplayQueue
from encoder import EncoderControl
from remote import RemoteControl
from squeezebox import SqueezeboxControl

# TODO:
# [] OLED display integration
# [] streamer mode:
#    [] song artist/title


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log",
        default="WARNING",
        help="sets logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--config-path", help="path to config file")
    args = parser.parse_args()
    logging.basicConfig(level=args.log)

    cwd = Path(__file__).resolve().parent
    config_path = (
        Path(args.config_path) if args.config_path else cwd.joinpath("config.yaml")
    )
    config = yaml.safe_load(config_path.read_text())

    displayctl = DisplayControl()
    display_queue = DisplayQueue(displayctl)
    ctl = Control(cwd, config, display_queue)
    squeezectl = SqueezeboxControl(config["squeezebox"], ctl)
    remotectl = RemoteControl(config["remote"], ctl, mediactl=squeezectl)
    EncoderControl(remotectl)

    await asyncio.gather(
        squeezectl.refresh_loop(),
        remotectl.refresh_loop(),
        display_queue.refresh_loop(),
    )
    displayctl.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    sys.exit(loop.run_until_complete(main()))
