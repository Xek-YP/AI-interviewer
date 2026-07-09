from sqlalchemy.orm import (
    DeclarativeBase,
    declared_attr,
)

class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
