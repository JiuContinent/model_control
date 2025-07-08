# src/app/services/crud_service.py
"""
封装所有与数据库 CRUD 相关的业务逻辑。
这是一个 Repository Pattern 的实现，将数据访问逻辑与 API 层解耦。
"""
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.mysql_models import Item
from app.models.schemas import ItemCreate

class CrudService:
    async def create_mysql_item(self, db: AsyncSession, item_data: ItemCreate) -> Item:
        """在 MySQL 中创建一个 Item"""
        db_item = Item(
            name=item_data.name,
            description=item_data.description
        )
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    async def get_mysql_item(self, db: AsyncSession, item_id: str) -> Optional[Item]:
        """从 MySQL 中获取一个 Item"""
        result = await db.execute(select(Item).filter(Item.id == item_id))
        return result.scalars().first()

    async def list_mysql_items(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Item]:
        """从 MySQL 中获取 Item 列表"""
        result = await db.execute(select(Item).offset(skip).limit(limit))
        return result.scalars().all()