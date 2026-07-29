Для создания миграции
python -m alembic revision --autogenerate -m "Initial migration"

Для применения миграции
python -m alembic upgrade head

Чтобы проверить создались ли таблицы
docker-compose exec db psql -U bot_admin_xek -d AI_sobes -c "\dt"

Для запуска бота
python main.py
