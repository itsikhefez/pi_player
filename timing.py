from time import time
import logging


def timer_func(func):
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        logging.info(f"Function {func.__name__!r} executed in {(t2-t1):.8f}s")
        return result

    return wrap_func
