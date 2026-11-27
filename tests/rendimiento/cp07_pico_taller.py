import os
import sys
from locust import LoadTestShape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from locustfile_taller import CP06FlujoMixtoTaller  # noqa: E402, F401


class FormaPicoCP07(LoadTestShape):
    """CP-TAL-PERF-07: Sube bruscamente de 10 a 50 usuarios en 10s (1 minuto total)."""

    def tick(self):
        run_time = self.get_run_time()
        if run_time < 15:
            return (10, 5)
        if run_time < 60:
            return (50, 4)
        return None