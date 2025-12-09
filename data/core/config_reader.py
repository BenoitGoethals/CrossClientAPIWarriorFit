import yaml
from pathlib import Path
from dataclasses import dataclass


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
class Config:
    database: DatabaseConfig


class ConfigReader:
    _instance: "ConfigReader | None" = None
    _config: Config | None = None

    def __new__(cls) -> "ConfigReader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str | Path | None = None):
        if self._config is None:
            if config_path is None:
                config_path = Path(__file__).parent.parent.parent/ "config/config.yml"
            self._load_config(Path(config_path))

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as file:
            raw_config = yaml.safe_load(file)

        self._config = Config(
            database=DatabaseConfig(**raw_config["database"])
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
