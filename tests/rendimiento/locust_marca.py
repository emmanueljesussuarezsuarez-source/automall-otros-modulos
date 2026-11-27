from locust import HttpUser, task, between

SESSION_COOKIE = "eyJjZWR1bGFfdXN1YXJpbyI6IjE4OTk4NzU0IiwiY29kX3JvbCI6MSwidXN1YXJpb19ub21icmUiOiJQZWRybyJ9.awc0IA.QiNQ_SxhWyM_KOoVgQjsQN8JdyM"

class UsuarioMarca(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.client.cookies.set("session", SESSION_COOKIE)

    @task
    def consultar_marcas(self):
        with self.client.get("/marcas/registro", catch_response=True) as resp:
            if "/login" in resp.url:
                resp.failure("Sesión expirada o cookie inválida (redirigió a /login)")
            elif resp.status_code != 200:
                resp.failure(f"Código inesperado: {resp.status_code}")
            else:
                resp.success()