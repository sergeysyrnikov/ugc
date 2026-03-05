# UGC
Cистема пользовательских опросов (UGC).

## API: Получить следующий вопрос опроса

**Эндпоинт**

- **URL**: `GET /api/surveys/{survey_id}/submissions/{submission_id}/next-question/`
- **Авторизация**: требуется (`Authorization: Bearer <JWT>`)

**Назначение**

Возвращает **следующий неотвеченный вопрос** для конкретной попытки прохождения опроса (`Submission`) в рамках указанного опроса (`Survey`).  
Если вопросы в опросе закончились, эндпоинт сообщает, что прохождение завершено.

**Правила и проверки**

- Если опрос с `survey_id` не найден → `404 Not Found` с телом:
  ```json
  {"detail": "Survey not found."}
  ```
- Если попытка `submission_id` не найдена → `404 Not Found`:
  ```json
  {"detail": "Submission not found."}
  ```
- Если попытка не принадлежит этому опросу → `400 Bad Request`:
  ```json
  {"detail": "Submission does not belong to this survey."}
  ```

**Логика выбора вопроса**

- Берутся все вопросы опроса, к которым **ещё нет ответов** в `SubmissionAnswer` для этой `submission`.
- Вопросы сортируются по полям `order`, затем `id`.
- Берётся **первый** такой вопрос.
- Если вопросов не осталось, считается, что опрос завершён.

**Ответы**

- Если следующий вопрос найден — `200 OK`:

  ```json
  {
    "question": {
      "id": 12,
      "text": "How satisfied are you with our product?",
      "type": "single_choice",
      "order": 1,
      "answers": [
        {"id": 101, "text": "Very satisfied", "order": 1},
        {"id": 102, "text": "Satisfied", "order": 2},
        {"id": 103, "text": "Neutral", "order": 3},
        {"id": 104, "text": "Dissatisfied", "order": 4}
      ]
    },
    "is_finished": false
  }
  ```

  - **`question.order`** — порядок вопроса в опросе.
  - **`answers[].order`** — порядок варианта ответа внутри вопроса (используется для отображения на фронтенде).

- Если вопросов больше нет — `200 OK`:

  ```json
  {
    "question": null,
    "is_finished": true
  }
  ```

## Краткий обзор основных эндпоинтов

- **Аутентификация**
  - `POST /api/auth/token/` — получить пару токенов JWT (access + refresh).
  - `POST /api/auth/token/refresh/` — обновить access-токен по refresh-токену.

- **Пользователи (`/api/users/`)**
  - `GET /api/users/` — список пользователей (зависит от прав доступа).
  - `POST /api/users/` — создание пользователя.
  - `GET /api/users/{id}/` — детальная информация о пользователе.
  - `PATCH /api/users/{id}/` — частичное обновление пользователя.
  - `DELETE /api/users/{id}/` — удаление пользователя.
  - `GET /api/users/me/` — текущий аутентифицированный пользователь.

- **Опросы**
  - `GET /api/surveys/{survey_id}/submissions/{submission_id}/next-question/` — следующий вопрос для прохождения опроса (см. раздел выше).

Полное описание схемы и всех полей доступно в интерактивной документации (см. ниже).

## Документация API

- Swagger UI: `http://localhost:8000/api/docs/swagger/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI схема: `http://localhost:8000/api/schema.json`

Документация генерируется с помощью `drf-yasg` и отражает фактические сериализаторы и вьюхи проекта.

## Запуск локально (без Docker)

Требования:

- Python 3.12+
- Установленный `uv`

Шаги:

```bash
cd ugc
uv sync

# Применить миграции
uv run python manage.py migrate

# (Опционально) создать суперпользователя
uv run python manage.py createsuperuser

# Запустить dev-сервер
uv run python manage.py runserver 127.0.0.1:8050
```

После запуска API будет доступно по адресу `http://127.0.0.1:8050/`.

## Запуск через Docker

Предполагается, что в корне проекта есть файл `env.dev` с переменными окружения.

```bash
cd ugc

# Собрать образ
docker build -t ugc .

# Запустить контейнер
docker run --env-file env.dev -p 8000:8000 ugc
```

После старта контейнера API и документация будут доступны по `http://localhost:8000/`.

## Тестирование

Для запуска тестов (pytest):

```bash
cd ugc
uv run pytest
```

В проекте используются тесты для API и моделей (например, в `accounts/tests/`), которые можно использовать как примеры ожидаемого поведения эндпоинтов.