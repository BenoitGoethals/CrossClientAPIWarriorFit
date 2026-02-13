import logging
from typing import Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.core.db_connection import DatabaseConnection
from src.data.model.db_model import Cross, Runner, User


class CrossRepository:
    """
    Handles operations related to cross entities and their runners.

    This class provides methods to manage cross entities and their runners, including retrieving,
    modifying, and saving data related to crosses and runners. It interacts with a database and
    maintains persistent storage of these entities. It also integrates logging for error handling.

    :ivar db: Manages the database connection and sessions.
    :type db: DatabaseConnection
    :ivar logger: Handles logging for error and activity tracking.
    :type logger: logging.Logger
    """

    def __init__(self):
        self._db = DatabaseConnection()
        self._logger = logging.getLogger(__name__)

    async def get_all_crosses(self) -> Any | None:
        """
        Asynchronously retrieves all unexecuted "Cross" entities from the database.

        This method queries the database to fetch all "Cross" entities where the
        'executed' attribute is set to False. The results are ordered by their IDs
        and include the related "runners" data using a lazy loading strategy. If
        an exception occurs during the database operation, it logs the error
        and returns None.

        :return: A list of unexecuted "Cross" entities, or None if an error occurs.
        :rtype: Any | None
        """
        async with self._db.session_maker() as session:
            stmt = select(Cross).filter(Cross.executed == False).order_by(Cross.id).options(selectinload(Cross.runners))
            try:
                result = await session.scalars(stmt)
                return result.all()
            except SQLAlchemyError as e:
                self._logger.error("Database error fetching crosses: %s", e)
                return None

    async def get_cross(self, id_cross: int) -> Cross | None:
        """
        Asynchronously retrieves a `Cross` object by its unique identifier. This
        operation queries the database for a specific `Cross` record and includes
        its associated `runners` relationships using `selectinload` for performance
        optimization. If found, the method returns the `Cross` object; otherwise, it
        returns `None`.

        :param id_cross: The unique identifier of the `Cross` object to retrieve.
        :type id_cross: int
        :return: A `Cross` object if found, or `None` if no match exists in the database.
        :rtype: Cross | None
        """
        async with self._db.session_maker() as session:
            stmt = select(Cross).where(Cross.id == id_cross).options(selectinload(Cross.runners))
            try:
                result = await session.scalars(stmt)
                return result.one_or_none()
            except SQLAlchemyError as e:
                self._logger.error("Database error fetching cross %s: %s", id_cross, e)
                return None

    async def get_user_credentials(self,username:str)->User|None:
        async with self._db.session_maker() as session:
            stmt = select(User).where(User.username == username)
            try:
                result = await session.scalars(stmt)
                return result.one_or_none()
            except SQLAlchemyError as e:
                self._logger.error("Database error fetching user credentials for %s: %s", username, e)
                return None

    async def update_password_hash(self, username: str, new_hash: str) -> bool:
        """
        Updates the password hash for a user (used for bcrypt to Argon2 migration).

        :param username: The username of the user to update
        :param new_hash: The new Argon2 password hash
        :return: True if successful, False otherwise
        """
        async with self._db.session_maker() as session:
            stmt = select(User).where(User.username == username)
            try:
                result = await session.scalars(stmt)
                user = result.one_or_none()
                if user is None:
                    self._logger.error("User %s not found for password update", username)
                    return False
                user.password_hash = new_hash
                await session.commit()
                self._logger.info("Password hash upgraded to Argon2 for user: %s", username)
                return True
            except SQLAlchemyError as e:
                self._logger.error("Database error updating password hash for %s: %s", username, e)
                await session.rollback()
                return False

    async def add_runner(self, serial_number: str, cross_id: int) -> bool:
        """
        Adds a runner with the specified serial number to a cross.

        SECURITY: Uses parameterized queries to prevent SQL injection.

        :param serial_number: The serial number of the runner
        :param cross_id: The ID of the cross
        :return: True if successful, False otherwise
        """
        async with self._db.session_maker() as session:
            try:
                # Validate that the cross exists
                stmt = select(Cross).where(Cross.id == cross_id)
                result = await session.scalars(stmt)
                cross = result.one_or_none()

                if cross is None:
                    self._logger.error("Cross with id %s not found", cross_id)
                    return False

                # Create a new runner with the serial number
                # Using SQLAlchemy ORM with parameterized queries (SECURE)
                runner = Runner(
                    serial_number=serial_number,
                    running_time=0.0  # Default time, can be updated later
                )

                # Add runner to the session and the cross
                session.add(runner)
                cross.runners.append(runner)

                await session.commit()
                self._logger.info("Runner with serial %s added to cross %s", serial_number, cross_id)
                return True

            except IntegrityError as e:
                self._logger.error("Integrity constraint violated adding runner %s to cross %s: %s", serial_number, cross_id, e)
                await session.rollback()
                return False
            except SQLAlchemyError as e:
                self._logger.error("Database error adding runner %s to cross %s: %s", serial_number, cross_id, e)
                await session.rollback()
                return False

    async def get_all_runners(self, cross_id: int) -> list[Runner]:
        """
        Retrieves all runners for a specific cross.

        SECURITY: Uses parameterized queries to prevent SQL injection.

        :param cross_id: The ID of the cross
        :return: List of runners
        """
        async with self._db.session_maker() as session:
            try:
                stmt = select(Cross).where(Cross.id == cross_id).options(selectinload(Cross.runners))
                result = await session.scalars(stmt)
                cross = result.one_or_none()

                if cross is None:
                    self._logger.error("Cross with id %s not found", cross_id)
                    return []

                return list(cross.runners)

            except SQLAlchemyError as e:
                self._logger.error("Database error fetching runners for cross %s: %s", cross_id, e)
                return []

    async def add_cross(self, cross_id: int, cross: list[tuple[int, float]]):
        """
        Adds a new cross with runners.

        SECURITY: Uses parameterized queries to prevent SQL injection.

        :param cross_id: The ID of the cross
        :param cross: List of tuples containing (runner_id, running_time)
        """
        async with self._db.session_maker() as session:
            try:
                # Implementation would go here based on requirements
                # Currently a placeholder
                self._logger.warning("add_cross method not fully implemented")
                pass

            except SQLAlchemyError as e:
                self._logger.error("Database error adding cross %s: %s", cross_id, e)
                await session.rollback()

    async def save_recordings(self, cross_id, runners: List[Runner]):
        """
        Saves the provided runner recordings to the database, associating them with the specified cross ID.
        Marks the cross as executed upon successful addition of all runners.

        :param cross_id: The unique identifier for the cross to which runners are to be associated.
        :type cross_id: int
        :param runners: A list of Runner objects to be saved and associated with the given cross.
        :type runners: List[Runner]
        :return: None
        """
        async with self._db.session_maker() as session:
            try:
                stmt = select(Cross).where(Cross.id == cross_id).options(selectinload(Cross.runners))
                result = await session.scalars(stmt)
                cross = result.one_or_none()
                if cross is None:
                    self._logger.error("Cross with id %s not found", cross_id)
                    return
                for runner in runners:
                    cross.runners.append(runner)
                cross.executed = True
                await session.commit()
            except SQLAlchemyError as e:
                self._logger.error("Database error saving recordings for cross %s: %s", cross_id, e)
                await session.rollback()
                return
