from locust import HttpUser, task, between

SESSION_COOKIE = "eyJjZWR1bGFfdXN1YXJpbyI6IjE4OTk4NzU0IiwiY29kX3JvbCI6MSwidXN1YXJpb19ub21icmUiOiJQZWRybyJ9.awc0IA.QiNQ_SxhWyM_KOoVgQjsQN8JdyM"

class UsuarioVehiculo(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.client.cookies.set("session", SESSION_COOKIE)

    @task(3)
    def listar_vehiculos(self):
        with self.client.get("/vehiculos-lista", catch_response=True) as resp:
            if "/login" in resp.url:
                resp.failure("Sesión expirada o cookie inválida (redirigió a /login)")
            elif resp.status_code != 200:
                resp.failure(f"Código inesperado: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def vista_registro_vehiculo(self):
        with self.client.get("/vehiculos-registrar", catch_response=True) as resp:
            if "/login" in resp.url:
                resp.failure("Sesión expirada o cookie inválida (redirigió a /login)")
            elif resp.status_code != 200:
                resp.failure(f"Código inesperado: {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def historial_vehiculos(self):
        with self.client.get("/vehiculos-historial", catch_response=True) as resp:
            if "/login" in resp.url:
                resp.failure("Sesión expirada o cookie inválida (redirigió a /login)")
            elif resp.status_code != 200:
                resp.failure(f"Código inesperado: {resp.status_code}")
            else:
                resp.success()