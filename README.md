# Проект Фудграм

> Домен: localhost
>
> Логин: admin
>
> Почта: admin@example.com
> 
> Пароль: admin1234

---

## Описание проекта

Сервис позволяет:

- Создавать рецептыы
- Добавлять рецепты в избранное и список покупок
- Подписываться на других пользователей
- Скачивать список покупок

| Стек технологий                                                                   |
|-----------------------------------------------------------------------------------|
| Python 3.9<br>Django 3.2<br>React<br>Docker<br>Postgres 13.0<br>Gunicorn<br>Nginx |

---

## Запуск проекта в dev-режиме

- **Клонировать репозиторий**:

```
https://github.com/HermannRorshach/foodgram-project-react.git
```

---

- **В директории `infra` создать файл `.env`**:

```
SECRET_KEY='test_key1234'
DEBUG=False

DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
DB_HOST=db
DB_PORT=5432
```

---

- **Создать и запустить контейнер. Из директории `infra`**:

```
docker compose up -d
```

---

* _Проект доступен по адресу:_ http://localhost/
* _Документация доступна:_ http://localhost/api/docs/
