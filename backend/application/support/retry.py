import functools
import time


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0, dont_retry: tuple = ()):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except dont_retry:
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(base_delay * (2 ** attempt))
            raise last_exception
        return wrapper
    return decorator