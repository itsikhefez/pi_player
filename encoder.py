import asyncio
import pigpio

from remote import RemoteControl, RemoteButton

GPIO_A = 27
GPIO_B = 4
GPIO_SW = 25
DEBOUNCE = 300

GPIO_MAPPING = {
    GPIO_A: ["d", "D"],
    GPIO_B: ["c", "C"],
}
SEQUENCE_UP = ("CdcD", "dcDC", "cDCd", "DCdc")
SEQUENCE_DOWN = ("CDcd", "DcdC", "cdCD", "dCDc")
SEQ_LENGTH = 4


class RotaryEncoder:
    def __init__(
        self,
        up_callback=None,
        down_callback=None,
        sw_callback=None,
    ):
        self.up_callback = up_callback
        self.down_callback = down_callback
        self.sw_callback = sw_callback
        self.sequence = SEQUENCE_UP[0]

        self.pi = pigpio.pi()

        def setup_gpio(gpio):
            self.pi.set_glitch_filter(gpio, DEBOUNCE)
            self.pi.set_pull_up_down(gpio, pigpio.PUD_UP)
            self.pi.callback(gpio, pigpio.EITHER_EDGE, self.rotary_callback)

        setup_gpio(GPIO_A)
        setup_gpio(GPIO_B)

        self.pi.set_glitch_filter(GPIO_SW, DEBOUNCE)
        self.pi.set_pull_up_down(GPIO_SW, pigpio.PUD_UP)
        self.pi.callback(GPIO_SW, pigpio.FALLING_EDGE, self.sw_gpio_fall)

    def append_seq(self, s: str) -> None:
        self.sequence += s
        if len(self.sequence) >= SEQ_LENGTH:
            self.sequence = self.sequence[-SEQ_LENGTH:]

    def rotary_callback(self, gpio, level, tick):
        self.append_seq(GPIO_MAPPING[gpio][level])
        if level:
            if self.sequence in (SEQUENCE_UP):
                self.up_callback()
            elif self.sequence in (SEQUENCE_DOWN):
                self.down_callback()

    def sw_gpio_fall(self, a, b, c):
        self.sw_callback()


class EncoderControl:
    def __init__(self, remotectl: RemoteControl):
        def sw_short():
            asyncio.run(
                remotectl.handle_keypress(
                    RemoteButton.GT_TEN,
                )
            )

        def up_cb():
            asyncio.run(remotectl.handle_keypress(RemoteButton.TUNE_UP, force=True))

        def down_cb():
            asyncio.run(remotectl.handle_keypress(RemoteButton.TUNE_DOWN, force=True))

        self.rotary = RotaryEncoder(
            up_callback=up_cb,
            down_callback=down_cb,
            sw_callback=sw_short,
        )
