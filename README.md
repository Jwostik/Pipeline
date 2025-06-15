[![PyPI version](https://badge.fury.io/py/jwostik-pipeliner.svg)](https://badge.fury.io/py/jwostik-pipeliner)
![Build Status](https://github.com/jwostik/Pipeline/workflows/run_tests/badge.svg)

# Pipeline

Универсальный движок для выполнения задач

## Обзор

Проект реализует механизм последовательного исполнения задач с REST-интерфейсом и обладает следующим функционалом:
* **Создание и конфигурация задач:** HTTP-запросы и SQL-запросы (PostgreSQL) - pydantic-модели с
пользовательскими jq-фильтрами
* **Надёжное исполнение цепочек задач:** управление статусами, повторные попытки
и хранение результатов
* **API-интерфейс на FastAPI:** создание задач, их запуск и отслеживание работы
* **Хранение данных в PostgreSQL:** хранение отдельных задач, данных и статусов каждого запуска задачи
* **Мониторинг производительности:** сбор метрик (prometheus) и логов (loki) для мониторинга (grafana) производительности
* **Модульность и расширяемость:** легко добавить новые типы стадий или интеграции
Pipeliner работает на 8000 порту.

## Зависимости
- PostgreSQL
- Loki
- Prometheus
- Grafana

## Docker

```
docker build -t pipeline_image .
docker build -t consumer_image -f DockerfileConsumer .
docker compose up
```

## Пример работы
* Создание задачи
```
curl -X 'POST' http://localhost:8000/pipeline  -H 'accept: application/json'  -H 'Content-Type: application/json' -d '{"pipeline_name":"Authorization","stages":[{"type":"HTTP","params":{"url_path":"server.com/users/${path1}","method":"POST","body":'{"login":".login","password":".password"}',"return_values":{"user_id":".user_id"},"return_codes":[200]}},{"type":"HTTP","params":{"url_path":"server.com/auth","method":"POST","body":'{"user_id":".user_id"}',"return_values":{"jwt":".jwt"},"return_codes":[200]}}]}'
```
Возвращается идентификатор созданной задачи
* Получение данных задачи
```
curl -X 'GET' http://localhost:8000/pipeline?pipeline_name=<Имя_задачи>
```
Возвращается описание стадий задачи
* Запуск задачи с пользовательскими данными
```
curl -X 'POST' http://localhost:8000/job?pipeline_name=<Имя_задачи> -H 'accept: application/json'  -H 'Content-Type: application/json' -d '{"path_key1": ".path_value1","path_key2": ".path_value2","query_key1": ".query_value1","query_key2": ".query_value2","data_key1": ".data_value1","data_key2": ".data_value2"}'
```
Возвращается идентификатор запущенной задачи
* Проверка статуса задачи
```
curl -X 'GET' http://localhost:8000/job?job_id=<Идентификатор_запущенной_задачи>
```
Возвращается информацию о запущенной задаче: ее статус, номер текущей стадии, полученные ошибки при выполнении
