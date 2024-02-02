# foodgram
![example workflow](https://github.com/Michelin90/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Автор:

Михаил [Michelin90](https://github.com/Michelin90) Хохлов

## Описание:

На сервисе foodgram пользователи смогут публиковать рецепты, 
подписываться на публикации других пользователей, 
добавлять понравившиеся рецепты в список «Избранное», 
а перед походом в магазин скачивать сводный список продуктов, 
необходимых для приготовления одного или нескольких выбранных блюд.

## Как  локально запустить проект:

### Клонировать репозиторий:

```
git clone https://github.com/Michelin90/foodgram-project-react
```

### Шаблон наполнения .env файла:

В директории foodgram-project-react/infra создайте файл .env и наполните его по следющему шаблону:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<ваш пароль для базы данных>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<ваш секретный ключ для django проекта>
```

### Описание команд для запуска приложения в контейнерах:

Перейти в дерикторию запуска:

```
cd foodgram-project-react/infra
```

Запустить контейнеры:

```
sudo docker compose up -d
```

### Описание команд для заполнения базы данными:

Выполнить миграции:

```
sudo docker compose exec web python manage.py migrate
```
Создать суперпользователя:

```
sudo docker compose exec web python manage.py createsuperuser
```

Загрузить статику:

```
sudo docker compose exec web python manage.py collectstatic --no-input
```

Наполнить базу данными:
```
sudo docker compose exec web python manage.py loaddata fixtures.json
```

### Перейти на главную страницу приложения:
http://localhost/

### Подробная документация проекта:
http://localhost/api/docs/

