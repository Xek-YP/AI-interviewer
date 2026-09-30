Для создания миграции
python -m alembic revision --autogenerate -m "Initial migration"

Для применения миграции
python -m alembic upgrade head

Чтобы проверить создались ли таблицы
docker-compose exec db psql -U interview_user -d ai_interviewer -c "\dt"

Для запуска инфраструктуры (Postgres + Redis)
docker-compose up -d

Для запуска бота и админки
python main.py

Админка откроется в браузере:
http://127.0.0.1:8000/admin/login

