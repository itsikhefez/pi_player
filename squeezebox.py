import aiohttp
import asyncio
import logging

from typing import NamedTuple
from pysqueezebox import Server, Player
from control import Control, SongState
from media_player import MediaPlayerOp


class SqueezeboxConfig(NamedTuple):
    lms_server_ip: str
    polling_sleep: float
    client_name: str


class SqueezeboxControl:
    def __init__(self, config: dict, ctl: Control) -> None:
        self.ctl = ctl
        self.pending: MediaPlayerOp = None
        self.cond = asyncio.Condition()
        self.curr_song_state = SongState()
        self.config = SqueezeboxConfig(
            lms_server_ip=config["lms_server_ip"],
            polling_sleep=config["polling_sleep"],
            client_name=config["client_name"],
        )

    async def op(self, op: MediaPlayerOp) -> None:
        async with self.cond:
            if self.pending:
                logging.debug("op '%s' initiated while pending is not None", op)
                return

            self.pending = op
            self.cond.notify()

    async def handle_op(self, player: Player) -> None:
        try:
            async with self.cond:
                async with asyncio.timeout(self.config.polling_sleep):
                    await self.cond.wait()

                match self.pending:
                    case MediaPlayerOp.PREV:
                        if player.current_index == 0:
                            logging.info("PREV noop")
                            return
                        await player.async_index("-1")
                    case MediaPlayerOp.NEXT:
                        if player.current_index + 1 == player.playlist_tracks:
                            logging.info("NEXT noop")
                            return
                        await player.async_index("+1")
                    case MediaPlayerOp.PLAY:
                        await player.async_play()
                    case MediaPlayerOp.STOP:
                        await player.async_stop()
                    case MediaPlayerOp.PAUSE:
                        await player.async_toggle_pause()
                    case _:
                        raise Exception(f"{self.pending} not assigned")
                logging.info("handle_op. %s", self.pending)
        except TimeoutError:
            # in most cases the remote is not pressed so this will time-out
            return
        finally:
            self.pending = None

    async def player_update(self, player: Player) -> None:
        await player.async_update()
        song_state = SongState(
            album=player.album,
            artist=player.artist,
            title=player.title,
            image_url=player.image_url,
        )
        if self.curr_song_state != song_state:
            self.curr_song_state = song_state
            await self.ctl.update_song_state(song_state)

        logging.debug(
            f"{player.artist} - [{player.album}] {player.title} / {player.image_url}"
        )

    async def loop(self):
        async with aiohttp.ClientSession() as session:
            lms = Server(session, self.config.lms_server_ip)
            player = await lms.async_get_player(name=self.config.client_name)
            logging.info("Started squeezebox listener")
            while True:
                for coro in asyncio.as_completed(
                    [
                        self.player_update(player),
                        self.handle_op(player),
                    ]
                ):
                    await coro
