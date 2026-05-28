import time
from collections import deque


class QuotaManager:
    def __init__(self, max_per_minute: int = 5, min_delay_seconds: float = 12.0):
        self.max_per_minute = max_per_minute
        self.min_delay = min_delay_seconds
        self._timestamps: deque[float] = deque()

    def wait_if_needed(self):
        now = time.time()

        while self._timestamps and self._timestamps[0] < now - 60:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_per_minute:
            wait = self._timestamps[0] + 60 - now
            if wait > 0:
                print(f"[QUOTA] Limite de {self.max_per_minute}/min atingido. Aguardando {wait:.0f}s...")
                time.sleep(wait)

        if self._timestamps:
            elapsed = now - self._timestamps[-1]
            if elapsed < self.min_delay:
                wait = self.min_delay - elapsed
                print(f"[QUOTA] Delay mínimo entre requests. Aguardando {wait:.1f}s...")
                time.sleep(wait)

        self._timestamps.append(time.time())
