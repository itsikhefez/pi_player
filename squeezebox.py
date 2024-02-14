import aiohttp
import asyncio
import logging

from pysqueezebox import Server, Player
from display import DisplayControl

# TODO:
# [] display integration
# [] remote control
# [] volume
# [] streamer mode:
#    [] song artist/title/duration/sample rate
#    [] album art
# [] change input/mode -- TV/streamer/phono/cassette/Karaoke
# rotary encoder for volume

LMS_SERVER_IP = "192.168.1.90"
POLLING_SLEEP = 1
DEFAULT_PLAYER = "ubuntu"


class SqueezeboxControl:
    def __init__(self, displayctl: DisplayControl):
        self.displayctl = displayctl

    # async def next():
    async def loop(self):
        album_art_url = ""
        async with aiohttp.ClientSession() as session:
            lms = Server(session, LMS_SERVER_IP)
            player = await lms.async_get_player(name=DEFAULT_PLAYER)
            while True:
                await player.async_update()
                if album_art_url != player.image_url:
                    album_art_url = player.image_url
                    self.displayctl.album_art(album_art_url)
                    # self.displayctl.show_volume(volume=-40)

                logging.debug(
                    f"{player.artist} - [{player.album}] {player.title} / {player.image_url}"
                )
                await asyncio.sleep(POLLING_SLEEP)
