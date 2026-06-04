import yaml
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    driver: str
    host: str
    port: int
    username: str
    password: str
    database: str

    @property
    def connection_url(self) -> str:
        """Generate the SQLAlchemy async connection URL."""
        if "sqlite" in self.driver:
            return f"{self.driver}:///{self.database}"
        return f"{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ApiConfig:
    secret_key: str
    oauth2_secret_key: str = "default_secret_change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


@dataclass(frozen=True)
class MailConfig:
    host: str
    port: int
    username: str
    password: str
    sender_email: str
    use_ssl: bool = False
    use_tls: bool = False
    sender: str | None = None


@dataclass
class Config:
    database: DatabaseConfig
    api: ApiConfig
    mail: MailConfig


class ConfigReader:
    """Singleton class for loading application configuration."""

    _instance: "ConfigReader | None" = None
    _config: Config | None = None

    def __new__(cls) -> "ConfigReader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str | Path | None = None):
        if self._config is None:
            if config_path is None:
                # Check APP_ENV environment variable to determine config location
                app_env = os.getenv("APP_ENV", "development")
                if app_env == "docker":
                    # Running in Docker container
                    config_path = Path("/etc/CrossClientAPI")
                    if config_path.is_dir():
                        config_path = config_path / "config.yml"
                else:
                    # Running in IDE/development
                    config_path = Path(__file__).parent.parent / "config" / "config.yml"
            self._load_config(Path(config_path))

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        # If config_path is a directory, look for config.yml inside it
        if config_path.is_dir():
            config_path = config_path / "config.yml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as file:
            raw_config = yaml.safe_load(file)

        self._config = Config(
            database=DatabaseConfig(**raw_config["database"]),
            api=ApiConfig(**raw_config["api"]),
            mail=MailConfig(**raw_config["mail"]),
        )

    @property
    def config(self) -> Config:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config


# Convenience function
def get_config() -> Config:
    return ConfigReader().config
