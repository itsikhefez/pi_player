class SongState:
    def __init__(
        self,
        album: str = None,
        artist: str = None,
        title: str = None,
        time: int = 0,
        duration: int = 0,
        bitrate: int = 0,
        samplerate: str = None,
        image_url: str = None,
    ):
        self.album = album
        self.artist = artist
        self.title = title
        self.time = time
        self.length = duration
        self.bitrate = bitrate
        self.samplerate = samplerate
        self.image_url = image_url

    def __eq__(self, other) -> bool:
        return (
            self.album == other.album
            and self.artist == other.artist
            and self.title == other.title
        )

    def __str__(self) -> str:
        return (
            f"{self.artist}|{self.album}|{self.title}|{self.bitrate}|{self.samplerate}"
        )
