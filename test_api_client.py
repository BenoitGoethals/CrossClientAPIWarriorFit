#!/usr/bin/env python3
"""
WarriorFit API Test Client

This client tests all API endpoints with different authentication methods:
1. OAuth2 Password Flow (username/password)
2. API Key authentication

Tests role-based access control (PTI, ADMIN, APTI roles required)
"""

import httpx
import json
from typing import Optional, Dict, Any


class WarriorFitClient:
    """Client for WarriorFit API with authentication support."""

    def __init__(self, base_url: str = "https://localhost:8555", cert_path: Optional[str] = None):
        """
        Initialize the API client.

        :param base_url: Base URL of the API
        :param cert_path: Path to SSL certificate (optional, for self-signed certs)
        """
        self.base_url = base_url.rstrip('/')
        self.cert_path = cert_path
        self.access_token: Optional[str] = None
        self.api_key: Optional[str] = None

    def _get_verify_param(self):
        """Get the verify parameter for httpx (cert path or False)."""
        if self.cert_path:
            return self.cert_path
        return False  # For self-signed certificates

    def _get_client(self) -> httpx.Client:
        """Get httpx client with proper SSL configuration."""
        return httpx.Client(verify=self._get_verify_param(), timeout=30.0)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with username and password to get OAuth2 access token.

        :param username: Username
        :param password: Password
        :return: Token response
        """
        url = f"{self.base_url}/token"
        data = {
            "username": username,
            "password": password
        }

        print(f"\n🔐 Logging in as '{username}'...")
        try:
            with self._get_client() as client:
                response = client.post(url, data=data)
                response.raise_for_status()
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                print(f"✅ Login successful! Token expires in 30 minutes")
                return token_data
        except httpx.HTTPStatusError as e:
            print(f"❌ Login failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Login error: {e}")
            raise

    def set_api_key(self, api_key: str):
        """
        Set API key for authentication.

        :param api_key: API key from config
        """
        self.api_key = api_key
        print(f"\n🔑 API Key set: {api_key[:20]}...")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def get_crosses(self) -> list:
        """Get all crosses."""
        url = f"{self.base_url}/crosses"
        print(f"\n📋 GET {url}")

        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                print(f"✅ Success: Retrieved {len(data)} crosses")
                return data
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def get_cross(self, cross_id: int) -> Dict[str, Any]:
        """Get a specific cross by ID."""
        url = f"{self.base_url}/crosses/{cross_id}"
        print(f"\n🎯 GET {url}")

        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                print(f"✅ Success: Retrieved cross #{cross_id}")
                return data
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def get_runners(self, cross_id: int) -> list:
        """Get all runners for a cross."""
        url = f"{self.base_url}/crosses/runners/{cross_id}"
        print(f"\n🏃 GET {url}")

        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                print(f"✅ Success: Retrieved {len(data)} runners")
                return data
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    def save_recordings(self, cross_id: int, recordings: list) -> Dict[str, Any]:
        """Save cross recordings."""
        url = f"{self.base_url}/crosses/{cross_id}"
        print(f"\n💾 POST {url}")
        print(f"   Saving {len(recordings)} recordings")

        try:
            with self._get_client() as client:
                response = client.post(url, headers=self._get_headers(), json=recordings)
                response.raise_for_status()
                print(f"✅ Success: Recordings saved")
                return response.json() if response.text else {}
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error: {e}")
            raise


def print_banner(text: str):
    """Print a formatted banner."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_api():
    """Test the WarriorFit API with different scenarios."""

    # Initialize client
    client = WarriorFitClient(
        base_url="https://localhost:8555",
        cert_path="./src/certs/cert.pem"
    )

    # Test 1: API Key Authentication
    print_banner("TEST 1: API Key Authentication (Full Access)")
    try:
        client.set_api_key("warriorfit_cross_the_world")
        crosses = client.get_crosses()
        print(f"\n📊 Retrieved crosses: {json.dumps(crosses[:2] if len(crosses) > 2 else crosses, indent=2)}")
    except Exception as e:
        print(f"\n⚠️ API Key test failed: {e}")

    # Test 2: OAuth2 with PTI role
    print_banner("TEST 2: OAuth2 Authentication with PTI Role")
    try:
        # Clear API key
        client.api_key = None

        # Login (you'll need to provide valid credentials)
        username = input("\nEnter username (PTI/ADMIN/APTI role): ").strip()
        password = input("Enter password: ").strip()

        client.login(username, password)
        crosses = client.get_crosses()
        print(f"\n📊 User has access! Retrieved {len(crosses)} crosses")

        if crosses:
            # Get details of first cross
            first_cross = client.get_cross(crosses[0]['id'])
            print(f"\n🎯 First cross details:")
            print(json.dumps(first_cross, indent=2))

    except Exception as e:
        print(f"\n⚠️ OAuth2 test failed: {e}")

    # Test 3: Unauthorized access (no auth)
    print_banner("TEST 3: Unauthorized Access (No Authentication)")
    try:
        client.access_token = None
        client.api_key = None
        client.get_crosses()
    except Exception as e:
        print(f"✅ Expected failure - API correctly blocks unauthorized access")

    # Test 4: Save recordings (if user has write access)
    print_banner("TEST 4: Save Recordings (Write Access)")
    try:
        # Re-authenticate
        client.set_api_key("warriorfit_cross_the_world")

        sample_recordings = [
            {"serial_number": "TEST001", "running_time": 125.5},
            {"serial_number": "TEST002", "running_time": 132.3}
        ]

        choice = input("\nDo you want to test saving recordings? (y/n): ").strip().lower()
        if choice == 'y':
            cross_id = int(input("Enter cross ID to save recordings to: ").strip())
            result = client.save_recordings(cross_id, sample_recordings)
            print(f"\n✅ Recordings saved successfully!")
        else:
            print("\n⏭️  Skipped save recordings test")

    except Exception as e:
        print(f"\n⚠️ Save recordings test failed: {e}")

    print_banner("API Tests Complete")


def interactive_mode():
    """Interactive mode for manual API testing."""
    client = WarriorFitClient(
        base_url="https://localhost:8555",
        cert_path="./src/certs/cert.pem"
    )

    print_banner("WarriorFit API - Interactive Mode")

    while True:
        print("\n" + "=" * 70)
        print("Options:")
        print("  1. Login with username/password")
        print("  2. Set API key")
        print("  3. Get all crosses")
        print("  4. Get specific cross")
        print("  5. Get runners for a cross")
        print("  6. Save recordings")
        print("  7. Clear authentication")
        print("  0. Exit")
        print("=" * 70)

        choice = input("\nSelect option: ").strip()

        try:
            if choice == "1":
                username = input("Username: ").strip()
                password = input("Password: ").strip()
                client.login(username, password)

            elif choice == "2":
                api_key = input("API Key: ").strip()
                client.set_api_key(api_key)

            elif choice == "3":
                crosses = client.get_crosses()
                print(f"\n📊 Crosses:\n{json.dumps(crosses, indent=2)}")

            elif choice == "4":
                cross_id = int(input("Cross ID: ").strip())
                cross = client.get_cross(cross_id)
                print(f"\n🎯 Cross:\n{json.dumps(cross, indent=2)}")

            elif choice == "5":
                cross_id = int(input("Cross ID: ").strip())
                runners = client.get_runners(cross_id)
                print(f"\n🏃 Runners:\n{json.dumps(runners, indent=2)}")

            elif choice == "6":
                cross_id = int(input("Cross ID: ").strip())
                recordings = []
                while True:
                    serial = input("Serial number (or 'done'): ").strip()
                    if serial.lower() == 'done':
                        break
                    time = float(input("Running time (seconds): ").strip())
                    recordings.append({"serial_number": serial, "running_time": time})

                if recordings:
                    result = client.save_recordings(cross_id, recordings)
                    print(f"\n✅ Result:\n{json.dumps(result, indent=2)}")

            elif choice == "7":
                client.access_token = None
                client.api_key = None
                print("✅ Authentication cleared")

            elif choice == "0":
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid option")

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import sys

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   WarriorFit API Test Client                         ║
║                                                                      ║
║  Tests authentication and role-based access control                 ║
║  Supports: OAuth2 (username/password) and API Key                   ║
║  HTTP Client: httpx (modern, async-ready)                           ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        print("\nRunning automated tests...\n")
        test_api()
        print("\n💡 Tip: Run with --interactive flag for manual testing")
        print("   python test_api_client.py --interactive")
