# Project Notes

## Important Changes

**2026-02-08** — Начало работы над проектом Telegram-бот «Главная цель дня»
**2026-02-08** — Создана структура проекта со всеми модулями
**2026-02-08** — Добавлен .env файл для переменных окружения (python-dotenv)
**2026-02-08** — Добавлены админ-команды с проверкой доступа (возвращает user_id если нет прав)

## Краткое описание проекта

Telegram-бот для постановки одной главной цели на день с напоминаниями и статистикой.

## Стек
- Python + aiogram
- SQLite
- APScheduler

## Структура
```
bot/
  main.py
  handlers/
  keyboards/
  database/
  texts.py
  config.py
  admins.txt
  .env
  scheduler.py
logs/
app.db
```

## Ключевые шаги создания бота

### 1. Создание структуры проекта
- Папки: `bot/`, `bot/handlers/`, `bot/keyboards/`, `bot/database/`, `logs/`
- Основные файлы: `main.py`, `config.py`, `texts.py`, `scheduler.py`

### 2. Конфигурация (config.py)
- Пути к файлам (BASE_DIR, DB_PATH, LOGS_DIR)
- Загрузка переменных из `.env` через `python-dotenv`
- Настройки: BOT_TOKEN, TIMEZONE, REMINDER_TIMES

### 3. База данных (database/)
- `db.py` — инициализация SQLite, создание таблиц
- `users.py` — CRUD для пользователей
- `goals.py` — CRUD для целей, статистика, закрытие дня

### 4. Клавиатуры (keyboards/)
- `main_menu.py` — главное меню (Цель на сегодня/завтра, Статистика)
- `goal_actions.py` — inline-кнопки для управления целью

### 5. Обработчики (handlers/)
- `start.py` — /start, регистрация пользователя
- `goals.py` — создание, редактирование, удаление целей (FSM)
- `stats.py` — личная статистика
- `admin.py` — админ-команды (/admin_stats, /admin_export, /admin_metric)

### 6. Планировщик (scheduler.py)
- APScheduler для напоминаний (09:00, 13:00, 17:00, 21:00, 23:59)
- Автоматическое закрытие дня в 00:01 (pending → failed)

### 7. Тексты (texts.py)
- Все строки вынесены в отдельный файл для удобства локализации

### 8. Запуск
```bash
py -m venv venv
./venv/Scripts/pip install -r requirements.txt
# Заполнить bot/.env (BOT_TOKEN)
./venv/Scripts/python bot/main.py
```

## Статус
**MVP готов и протестирован** ✅
