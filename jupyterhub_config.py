import os
from dockerspawner import DockerSpawner
from jupyterhub.auth import DummyAuthenticator

c = get_config()

# ---------- Spawner ----------
c.JupyterHub.spawner_class = DockerSpawner
c.DockerSpawner.image = os.environ.get("DOCKER_JUPYTER_IMAGE", "nbgrader-singleuser:latest")
c.DockerSpawner.notebook_dir = "/home/jovyan"

# внутренняя сеть и IP
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = os.environ.get("DOCKER_NETWORK_NAME", "jupyter_nbgrader_default")

c.DockerSpawner.pull_policy = "never"

# общие / личные тома
c.DockerSpawner.volumes = {
    "nb-exchange": {"bind": "/srv/nbgrader/exchange", "mode": "rw"},
    "courses-{username}": {"bind": "/home/jovyan", "mode": "rw"},
}


# ВАЖНО: НЕ переопределяем команду — используем дефолтный entrypoint образа
# Просто запускаем контейнер сразу под пользователем 1000 (jovyan)
c.DockerSpawner.extra_create_kwargs = {"user": "1000:100"}

# таймауты и автоудаление
c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 120
c.DockerSpawner.remove = True

# ---------- Hub ----------
c.JupyterHub.bind_url = "http://:8000"
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = "nbgrader-hub"

# ---------- Auth (DEV) ----------
c.JupyterHub.authenticator_class = DummyAuthenticator
c.DummyAuthenticator.password = os.environ.get("DUMMY_SHARED_PASSWORD", None)
admin_user = os.environ.get("JUPYTERHUB_ADMIN", "instructor")
c.Authenticator.admin_users = {admin_user}
