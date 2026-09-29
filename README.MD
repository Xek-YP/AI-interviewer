Для создания миграции
python -m alembic revision --autogenerate -m "Initial migration"

Для применения миграции
python -m alembic upgrade head

Чтобы проверить создались ли таблицы
docker-compose exec db psql -U interview_user -d ai_interviewer -c "\dt"

Для запуска бота и админки
python main.py

Админка откроется в браузере:
http://127.0.0.1:8000/admin/login

Логин/пароль задаются в `.env`:
ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY

Только админка (без бота):
uvicorn admin.app:app --host 127.0.0.1 --port 8000
