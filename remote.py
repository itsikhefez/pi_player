import evdev
import logging

"""
Remote control functionality
3) Volume inc/dec -- coarse (1.5dB) and fine (0.5dB)
4) Mute/dim
1) Direct input select

2) Input prev/next
5) Display toggle -- album art/song info/volume/system (capture rate, playback rate, etc)
6) EQ on/off
7) Next/prev song
8) Play/pause
"""

INPUT_DEVICE = "/dev/input/event0"


class RemoteControl:
    device: evdev.InputDevice

    def __init__(self):
        self.device = evdev.InputDevice(INPUT_DEVICE)
        logging.info(self.device)

    async def loop(self):
        async for event in self.device.async_read_loop():
            print(event)
