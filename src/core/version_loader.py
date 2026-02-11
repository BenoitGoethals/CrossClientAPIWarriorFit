"""Version loader utility."""
import yaml
from pathlib import Path


def load_version() -> str:
    """
    Loads the application's version information from a YAML file. This function attempts to locate
    a file named 'version.yaml' in the parent directory chain. If the file exists, it reads and parses
    the file's contents to extract the 'version' field. If the file is not found, or any parsing
    or key access errors occur, a default version of '0.0.0' is returned.

    :raises FileNotFoundError: If the version.yaml file is missing when attempting to read.
    :raises yaml.YAMLError: If there is an issue with parsing the YAML file contents.
    :raises KeyError: If the required 'version' key is not present in the parsed data.

    :return: A string representing the application version extracted from the YAML file or the
    default value of '0.0.0'.
    :rtype: str
    """
    try:
        version_file = Path(__file__).parent.parent.parent / "version.yaml"
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_data = yaml.safe_load(f)
                return version_data.get('version', '0.0.0')
        else:
            return '0.0.0'
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        return '0.0.0'
