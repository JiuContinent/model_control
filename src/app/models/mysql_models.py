# src/app/models/mysql_models.py
"""
SQLAlchemy ORM 模型。
定义了数据库表的结构和关系。
"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text
import uuid

class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)