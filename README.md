# JupyterHub + nbgrader (DockerSpawner) — готовый шаблон

## Быстрый старт

```bash
make build            # собрать образ single-user с nbgrader
make up               # запустить JupyterHub
make init-exchange    # создать и подготовить общий exchange (chmod 1777)
make init-course      # положить стартовый курс 'mycourse' в домашний admin'а
make instructor-login # вывести ссылку и доступ
```