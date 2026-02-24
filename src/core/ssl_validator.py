"""SSL certificate validation utilities."""

import logging
import subprocess
from pathlib import Path
from datetime import datetime

auth_logger = logging.getLogger("auth")


def validate_ssl_certificates(cert_path: str, key_path: str) -> dict:
    """
    Validate SSL certificates before starting the server.

    Checks:
    - Certificate and key files exist
    - Certificate is not expired
    - Certificate and key match
    - Files are readable

    :param cert_path: Path to certificate file
    :param key_path: Path to private key file
    :return: Dict with validation results
    :raises SystemExit: If validation fails critically
    """
    results = {"valid": True, "warnings": [], "errors": []}

    # Check if files exist
    cert_file = Path(cert_path)
    key_file = Path(key_path)

    if not cert_file.exists():
        results["errors"].append(f"Certificate file not found: {cert_path}")
        results["valid"] = False
        auth_logger.error(f"Certificate file not found: {cert_path}")

    if not key_file.exists():
        results["errors"].append(f"Private key file not found: {key_path}")
        results["valid"] = False
        auth_logger.error(f"Private key file not found: {key_path}")

    if not results["valid"]:
        auth_logger.error("SSL CERTIFICATE VALIDATION FAILED!")
        return results

    # Check if files are readable
    try:
        with open(cert_path, "r") as f:
            f.read(1)
    except Exception as e:
        auth_logger.error(f"Cannot read certificate file: {e}")
        results["errors"].append(f"Cannot read certificate file: {e}")
        results["valid"] = False

    try:
        with open(key_path, "r") as f:
            f.read(1)
    except Exception as e:
        auth_logger.error(f"Cannot read private key file: {e}")
        results["errors"].append(f"Cannot read private key file: {e}")
        results["valid"] = False

    if not results["valid"]:
        return results

    # Validate certificate expiry
    try:
        cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-enddate"]
        expiry_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        expiry_str = expiry_result.stdout.strip().replace("notAfter=", "")
        expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")

        days_until_expiry = (expiry_date - datetime.now()).days

        if days_until_expiry < 0:
            results["errors"].append(
                f"Certificate EXPIRED {abs(days_until_expiry)} days ago!"
            )
            results["valid"] = False
            auth_logger.error(f"Certificate EXPIRED {abs(days_until_expiry)} days ago!")
        elif days_until_expiry < 30:
            results["warnings"].append(
                f"Certificate expires in {days_until_expiry} days"
            )
        else:
            auth_logger.info(f"Certificate valid for {days_until_expiry} days")

    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Failed to validate certificate expiry: {e}")
        results["valid"] = False
        auth_logger.error(f"Failed to validate certificate expiry: {e}")
    except Exception as e:
        results["warnings"].append(f"Could not parse certificate expiry date: {e}")
        auth_logger.warning(f"Could not parse certificate expiry date: {e}")

    # Validate private key
    try:
        cmd = ["openssl", "rsa", "-in", key_path, "-check", "-noout"]
        key_validation_result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        auth_logger.info("Private key validation: OK")
    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Private key validation failed: {e.stderr}")
        results["valid"] = False
        auth_logger.error(f"Private key validation failed: {e.stderr}")

    # Validate certificate and key match
    try:
        # Get certificate modulus
        cmd_cert = ["openssl", "x509", "-noout", "-modulus", "-in", cert_path]
        cert_result = subprocess.run(
            cmd_cert, capture_output=True, text=True, check=True
        )
        cert_modulus = cert_result.stdout.strip()

        # Get key modulus
        cmd_key = ["openssl", "rsa", "-noout", "-modulus", "-in", key_path]
        key_result = subprocess.run(cmd_key, capture_output=True, text=True, check=True)
        key_modulus = key_result.stdout.strip()

        if cert_modulus != key_modulus:
            results["errors"].append("Certificate and private key DO NOT MATCH!")
            results["valid"] = False
            auth_logger.error("Certificate and private key: DO NOT MATCH!")
        else:
            auth_logger.info("Certificate and private key: MATCH")

    except subprocess.CalledProcessError as e:
        results["errors"].append(f"Failed to verify certificate/key match: {e}")
        results["valid"] = False
        auth_logger.error(f"Failed to verify certificate/key match: {e}")

    return results
