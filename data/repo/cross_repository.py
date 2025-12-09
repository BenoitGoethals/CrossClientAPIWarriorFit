import logging
from typing import Any
from sqlalchemy import select

from data.core.db_connection import DatabaseConnection
from data.model.db_model import Cross, Runner

class CrossRepository:


    def __init__(self):
        self._db = DatabaseConnection()
        self._logger = logging.getLogger(__name__)

    async def get_all_crosses(self) -> Any | None:
        async with self._db.session_maker() as session:
            stmt = select(Cross).order_by(Cross.id)
            try:
                result = await session.scalars(stmt)
                return result.all()
            except Exception as e:
                self._logger.error(e)
                return None

    async def get_cross(self, id_cross: int) -> Cross | None:
        async with self._db.session_maker() as session:
            stmt = select(Cross).where(Cross.id == id_cross)
            try:
                result = await session.scalars(stmt)
                return result.one_or_none()
            except Exception as e:
                self._logger.error(e)
                return None

    async def add_runner(self, serial_number: str, cross_id: int) -> bool:
        pass

    async def get_all_runners(self, cross_id: int) -> list[Runner]:
        pass