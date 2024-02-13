import aiohttp
import asyncio

from pysqueezebox import Server, Player

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


class SqueezeboxControl():
    lms: Server
    player: Player
    
    async def next():


    async def squeezebox_loop():
        # while True:
        async with aiohttp.ClientSession() as session:
            lms = Server(session, LMS_SERVER_IP)
            player = await lms.async_get_player(name=DEFAULT_PLAYER)
            await player.async_update()
            print(f"{player.artist} - [{player.album}] {player.title} / {player.image_url}")
            await asyncio.sleep(POLLING_SLEEP)
