## Prometheus и Grafana для UGC

Этот стек предназначен для локального мониторинга Django‑приложения UGC через эндпоинт `/metrics`.

### Предварительные условия

- Django‑приложение запущено локально и отдаёт метрики по `http://localhost:8050/metrics` (см. существующий `Dockerfile` и env.dev).
- Установлен Docker и Docker Compose.

### Запуск Prometheus и Grafana

Из корня репозитория выполните:

```bash
docker compose -f monitoring/docker-compose.yml up -d
```

После запуска будут доступны:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (логин/пароль по умолчанию: `admin` / `admin`)

### Настройка источника данных в Grafana

1. Откройте `http://localhost:3000` и войдите под `admin` / `admin`.
2. Создайте Data Source типа **Prometheus**.
3. В поле URL укажите: `http://localhost:9090`.
4. Сохраните источник и протестируйте соединение.

Далее можно импортировать/создавать дашборды на основе метрик `ugc_*` (HTTP, бизнес‑метрики и т.д.). Позже JSON‑экспорты дашбордов рекомендуется сохранять в каталоге `monitoring/dashboards/`.

