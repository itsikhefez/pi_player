import aiohttp
import asyncio
import logging

from pysqueezebox import Server, Player
from control import Control, SongState

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
    def __init__(self, ctl: Control) -> None:
        self.ctl = ctl

    # async def next():
    async def loop(self):
        curr_song_state = SongState()
        album_art_url = ""
        async with aiohttp.ClientSession() as session:
            lms = Server(session, LMS_SERVER_IP)
            player = await lms.async_get_player(name=DEFAULT_PLAYER)
            logging.info("started squeezebox listener...")
            while True:
                await player.async_update()
                song_state = SongState(
                    album=player.album,
                    artist=player.artist,
                    title=player.title,
                    image_url=player.image_url,
                )
                if curr_song_state != song_state:
                    curr_song_state = song_state
                    await self.ctl.update_song_state(song_state)

                logging.debug(
                    f"{player.artist} - [{player.album}] {player.title} / {player.image_url}"
                )
                await asyncio.sleep(POLLING_SLEEP)
