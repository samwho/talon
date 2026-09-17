import queue
import threading
from typing import Callable, Generic, TypeVar, cast

from talon import cron

T = TypeVar("T")


class LatestOnlyRefresh(Generic[T]):
    """Debounce refresh requests and publish only the latest completed result."""

    def __init__(
        self,
        delay: str,
        query: Callable[[], T],
        publish: Callable[[T], None],
        on_error: Callable[[Exception], T],
    ) -> None:
        self._delay = delay
        self._query = query
        self._publish = publish
        self._on_error = on_error
        self._generation = 0
        self._job = None
        self._running = False
        self._worker_started = False
        self._queue: queue.SimpleQueue[int] = queue.SimpleQueue()

    def request(self) -> None:
        """Request a refresh after the debounce delay."""
        self._generation += 1
        cron.cancel(self._job)
        self._job = cron.after(self._delay, self.run_now)

    def run_now(self) -> None:
        """Start the latest refresh unless one is already running."""
        cron.cancel(self._job)
        self._job = None
        if self._running:
            return

        self._running = True
        self._ensure_worker()
        self._queue.put(self._generation)

    def _ensure_worker(self) -> None:
        if self._worker_started:
            return
        self._worker_started = True
        threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="latest-only-refresh",
        ).start()

    def _worker_loop(self) -> None:
        while True:
            generation = self._queue.get()
            value: T | None = None
            error: Exception | None = None
            try:
                value = self._query()
            except Exception as caught:
                error = caught

            cron.after(
                "0ms",
                lambda generation=generation, value=value, error=error: self._finish(
                    generation, value, error
                ),
            )

    def _finish(
        self,
        generation: int,
        value: T | None,
        error: Exception | None,
    ) -> None:
        self._running = False
        if generation != self._generation:
            self.run_now()
            return

        if error is not None:
            value = self._on_error(error)
        self._publish(cast(T, value))
