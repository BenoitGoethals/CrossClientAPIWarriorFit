from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config_reader import get_config


class DatabaseConnection:
    """Singleton class for managing database connections."""

    _instance: "DatabaseConnection | None" = None
    _session_maker: async_sessionmaker[AsyncSession] | None = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the async engine and session maker."""
        config = get_config()

        engine = create_async_engine(
            config.database.connection_url,
            echo=True,  # Set to False in production
            pool_pre_ping=True,
        )

        self._session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Get the async session maker."""
        if self._session_maker is None:
            raise RuntimeError("Database connection not initialized")
        return self._session_maker

    async def get_session(self) -> AsyncSession:
        """Create a new async session."""
        return self.session_maker()
