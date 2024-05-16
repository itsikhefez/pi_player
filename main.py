import argparse
import logging
import sys
import asyncio
import yaml

from pathlib import Path
from control import Control
from display_modes import DisplayManager
from encoder import EncoderControl
from remote import RemoteControl
from squeezebox import SqueezeboxControl


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log",
        default="WARNING",
        help="sets logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--config-file", help="path to config file")
    args = parser.parse_args()
    logging.basicConfig(level=args.log)

    cwd = Path(__file__).resolve().parent
    config_file = (
        Path(args.config_file) if args.config_file else cwd.joinpath("config.yaml")
    )
    config = yaml.safe_load(config_file.read_text())

    ctl = None
    try:
        ctl = Control(config)
        squeezectl = SqueezeboxControl(config["squeezebox"], ctl)
        remotectl = RemoteControl(config["remote"], ctl, mediactl=squeezectl)
        EncoderControl(remotectl)

        await asyncio.gather(
            squeezectl.refresh_loop(),
            remotectl.refresh_loop(),
            ctl.display_manager.queue.refresh_loop(),
        )
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        if ctl:
            ctl.display_manager.queue.displayctl.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
