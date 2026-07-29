Для создания миграции
python -m alembic revision --autogenerate -m "Initial migration"

Для применения миграции
python -m alembic upgrade head

Чтобы проверить создались ли таблицы
docker-compose exec db psql -U interview_user -d ai_interviewer -c "\dt"

Для запуска бота
python main.py
