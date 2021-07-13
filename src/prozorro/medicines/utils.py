import logging
import asyncio
import functools

logger = logging.getLogger(__name__)


def async_retry(tries: int = -1, exceptions: Exception = Exception,
                delay: int = 0, max_delay: int = None, backoff: int = 1):
    """
    Retry async function calls
    """
    def func_wrapper(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            while True:
                try:
                    result = await f(*args, **kwargs)
                except exceptions as exc:
                    _tries -= 1
                    if not _tries:
                        raise exc
                    else:
                        logger.warning(
                            f"Retry {f} in {_delay}s because of {exc}")
                        await asyncio.sleep(_delay)

                        _delay *= backoff
                        if max_delay is not None:
                            _delay = min(_delay, max_delay)
                else:
                    return result
        return wrapper
    return func_wrapper
