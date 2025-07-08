# src/app/api/crud.py
"""
API 路由 - 针对 MySQL 的 CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mysql import get_db_session
from app.services.crud_service import CrudService
from app.models.schemas import ItemSchema, ItemCreate
from app.api import deps

router = APIRouter()

@router.post("/items", response_model=ItemSchema, status_code=201)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db_session),
    service: CrudService = Depends(deps.get_crud_service)
):
    """创建新的 Item"""
    return await service.create_mysql_item(db=db, item_data=item_in)

@router.get("/items", response_model=List[ItemSchema])
async def list_items(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    service: CrudService = Depends(deps.get_crud_service)
):
    """获取 Item 列表"""
    return await service.list_mysql_items(db=db, skip=skip, limit=limit)

@router.get("/items/{item_id}", response_model=ItemSchema)
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db_session),
    service: CrudService = Depends(deps.get_crud_service)
):
    """通过 ID 获取单个 Item"""
    item = await service.get_mysql_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item