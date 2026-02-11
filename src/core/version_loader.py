"""Version loader utility."""
import logging

import yaml
from pathlib import Path


def load_version() -> str:
    logger = logging.getLogger(__name__)
    """
    Load version from version.yaml file.

    Searches for version.yaml in multiple locations:
    1. /app/version.yaml (Docker environment)
    2. Project root (relative to this file)
    3. Current working directory

    :return: Version string (e.g., "0.0.2")
    """
    try:
        # List of possible locations for version file
        possible_paths = [
            Path("/app/version.yaml"),  # Docker environment
            Path("/app/version.yml"),   # Docker environment (alternative)
            Path(__file__).parent.parent.parent / "version.yaml",  # Project root
            Path(__file__).parent.parent.parent / "version.yml",   # Project root (alternative)
            Path.cwd() / "version.yaml",  # Current working directory
            Path.cwd() / "version.yml",   # Current working directory (alternative)
        ]

        for version_file in possible_paths:
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_data = yaml.safe_load(f)
                    version = version_data.get('version', '0.0.0')
                    return version

        return '0.0.0'
    except (FileNotFoundError, yaml.YAMLError, KeyError, OSError) as e:
        logger.exception('Failed to load version from version.yaml: %s', e)
        return '0.0.0'
