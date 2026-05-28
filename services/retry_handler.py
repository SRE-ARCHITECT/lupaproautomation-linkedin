import time
import random

RETRY_DELAYS = [5, 15, 30]

RETRYABLE_KEYWORDS = [
    "429", "resource_exhausted", "timeout", "rate limit",
    "too many requests", "quota", "unavailable", "connection",
    "500", "502", "503", "service unavailable", "temporary",
    "deadline exceeded", "capacity", "overloaded",
]


def is_retryable_error(error: Exception) -> bool:
    error_str = str(error).lower()
    return any(kw in error_str for kw in RETRYABLE_KEYWORDS)


def retry_with_backoff(func, *args, **kwargs):
    last_error = None
    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            result = func(*args, **kwargs)
            if result is not None:
                return result
        except Exception as e:
            last_error = e
            if is_retryable_error(e):
                if attempt < len(RETRY_DELAYS) - 1:
                    jitter = random.uniform(0.1, delay * 0.1)
                    total_delay = delay + jitter
                    print(f"[RETRY] Tentativa {attempt + 1}/{len(RETRY_DELAYS)} - aguardando {total_delay:.0f}s... [{str(e)[:100]}]")
                    time.sleep(total_delay)
                else:
                    print(f"[RETRY] Tentativas esgotadas para este provider.")
                    raise
            else:
                raise
    raise last_error or RuntimeError("retry_with_backoff: no result and no error")
