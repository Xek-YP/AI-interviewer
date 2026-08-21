Для создания миграции
python -m alembic revision --autogenerate -m "Initial migration"

Для применения миграции
python -m alembic upgrade head

Чтобы проверить создались ли таблицы
docker-compose exec db psql -U bot_admin_xek -d AI_sobes -c "\dt"

Для запуска бота
python main.py

для добавления тестовых категорий:
INSERT INTO question_categories (name, is_active) VALUES ('ООП', True), ('Структуры данных и алгоритмы', True), ('Базовые концепции и принципы', True), ('django', True), ('Архитектурные вопросы', True);
