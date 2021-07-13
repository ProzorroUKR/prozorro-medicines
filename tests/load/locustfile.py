from locust import HttpUser, task, constant

AUTH = ("broker", "broker")


class MedicinesUser(HttpUser):

    wait_time = constant(0)

    @task
    def registries(self):
        for name in ("inn", "atc", "inn2atc", "atc2inn"):
            result = self.client.get(f"/api/1.0/registry/{name}.json", auth=AUTH)
            if result.status_code != 200:
                print(result.text)
