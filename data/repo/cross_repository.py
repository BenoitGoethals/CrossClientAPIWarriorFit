import logging
from typing import Any
from sqlalchemy import select

from data.core.db_connection import DatabaseConnection
from data.model.db_model import Cross, Runner, CrossRunners


class CrossRepository:


    def __init__(self):
        self._db = DatabaseConnection()
        self._logger = logging.getLogger(__name__)

    async def get_all_crosses(self) -> Any | None:
        async with self._db.session_maker() as session:
            stmt = select(Cross).filter(Cross.executed==False).order_by(Cross.id)
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

    async def add_cross(self, cross_id:int, cross:list[tuple[int,float]]):
        pass

        # ... existing code ...

    async def save_recordings(self, cross_id, recordings):
        async with self._db.session_maker() as session:
            stmt = select(Cross).where(Cross.id == cross_id)
            result = await session.scalars(stmt)
            cross = result.one_or_none()

            if cross is None:
                self._logger.error(f"Cross with id {cross_id} not found")
                return

            for recording in recordings:
                runner = Runner(serial_number=None, running_time=recording.running_time)
                cross.runners.append(runner)

            await session.commit()