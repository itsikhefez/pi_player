import time


class TokenBucket:
    def __init__(self, tokens, time_unit):
        self.tokens = tokens
        self.time_unit = time_unit
        self.bucket = tokens
        self.last_check = time.time()

    def has_tokens(self) -> bool:
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current

        self.bucket = self.bucket + time_passed * (self.tokens / self.time_unit)
        if self.bucket > self.tokens:
            self.bucket = self.tokens

        if self.bucket < 1:
            return False
        self.bucket = self.bucket - 1
        return True


class Debounce:
    def __init__(self, time_unit):
        self.time_unit = time_unit
        self.last_check = time.time()

    def has_tokens(self) -> bool:
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        return time_passed > self.time_unit
