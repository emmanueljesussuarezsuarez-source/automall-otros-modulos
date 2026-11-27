from locust import HttpUser, task, between

class UsuarioCatalogo(HttpUser):
    wait_time = between(1, 2)

    @task
    def ver_catalogo_publico(self):
        with self.client.get("/catalogo-ventas", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Código inesperado: {resp.status_code}")
            elif b"<html" not in resp.content.lower():
                resp.failure("La respuesta no contiene HTML válido")
            else:
                resp.success()