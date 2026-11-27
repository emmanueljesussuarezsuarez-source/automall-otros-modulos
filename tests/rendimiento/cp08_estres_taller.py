import os
import sys
from locust import LoadTestShape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from locustfile_taller import CP06FlujoMixtoTaller  # noqa: E402, F401


class FormaEstresCP08(LoadTestShape):
    """CP-TAL-PERF-08: Estrés progresivo de 5 a 100 usuarios en 2 minutos."""

    def tick(self):
        run_time = self.get_run_time()
        if run_time < 10:
            return (5, 5)
        if run_time < 130:
            progreso = (run_time - 10) / 120.0
            usuarios = 5 + round(95 * progreso)
            return (usuarios, 5)
        if run_time < 150:
            return (100, 5)
        return None