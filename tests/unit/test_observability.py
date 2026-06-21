"""Unit tests for observability and Prometheus metrics."""
from app.services.observability import Timer


class TestTimer:
    def test_timer_records_elapsed_ms(self):
        with Timer("test") as t:
            import time

            time.sleep(0.001)
        assert t.elapsed_ms is not None
        assert t.elapsed_ms > 0
        assert t.name == "test"

    def test_timer_zero_work(self):
        with Timer("quick") as t:
            pass
        assert t.elapsed_ms is not None
        assert t.elapsed_ms >= 0
