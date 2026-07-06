# MBS Payroll

Система расчёта заработной платы.

## Стек

| Слой      | Технологии                                                   |
| --------- | ------------------------------------------------------------ |
| Backend   | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, JWT |
| Frontend  | React 18, TypeScript, Vite, Material UI 6, React Router, Axios |
| Инфра     | Docker, Docker Compose                                       |

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone <repo-url> && cd MBS-Pay

# 2. Поднять сервисы
docker compose up --build

# 3. Открыть в браузере
#    Frontend : http://localhost:3000
#    Swagger  : http://localhost:8000/docs
#    ReDoc    : http://localhost:8000/redoc
```

## Структура проекта

```
MBS-Pay/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Роутеры API v1
│   │   ├── core/            # Конфигурация, БД, безопасность
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── schemas/         # Pydantic схемы
│   │   ├── migrations/      # Alembic миграции
│   │   └── main.py          # Точка входа FastAPI
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios-клиент
│   │   ├── components/      # Переиспользуемые компоненты
│   │   ├── pages/           # Страницы
│   │   ├── router/          # React Router
│   │   ├── theme/           # MUI тема
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── package.json
├── docker-compose.yml
├── .env
└── README.md
```

## Миграции (Alembic)

```bash
# Создать новую миграцию
docker compose exec backend alembic revision --autogenerate -m "description"

# Применить миграции
docker compose exec backend alembic upgrade head
```
