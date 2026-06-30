from __future__ import annotations
import hashlib
import logging
import httpx
from datetime import datetime, timedelta, timezone
import jwt

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, keycloak_url: str, realm: str, client_id: str, admin_user: str, admin_password: str) -> None:
        self._url = keycloak_url.rstrip('/')
        self._realm = realm
        self._client_id = client_id
        self._admin_user = admin_user
        self._admin_password = admin_password

    def get_admin_token(self) -> str:
        url = f"{self._url}/realms/master/protocol/openid-connect/token"
        data = {
            "client_id": "admin-cli",
            "username": self._admin_user,
            "password": self._admin_password,
            "grant_type": "password"
        }
        with httpx.Client() as client:
            resp = client.post(url, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]

    def create_user_in_keycloak(self, email: str, password: str, name: str) -> str:
        admin_token = self.get_admin_token()
        url = f"{self._url}/admin/realms/{self._realm}/users"
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        first_name = name.split(" ")[0]
        last_name = " ".join(name.split(" ")[1:]) if " " in name else ""
        
        user_data = {
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "credentials": [{"type": "password", "value": password, "temporary": False}]
        }
        
        with httpx.Client() as client:
            resp = client.post(url, json=user_data, headers=headers)
            if resp.status_code == 409:
                raise ValueError("User already exists in Identity Provider.")
            resp.raise_for_status()

            location = resp.headers.get("Location")
            if location:
                return location.split("/")[-1]
            
            get_resp = client.get(f"{url}?username={email}", headers=headers)
            get_resp.raise_for_status()
            users = get_resp.json()
            if users:
                return users[0]["id"]
            raise ValueError("Failed to retrieve user ID from Keycloak")

    def create_access_token(self, email: str, password: str) -> dict:
        url = f"{self._url}/realms/{self._realm}/protocol/openid-connect/token"
        data = {
            "client_id": self._client_id,
            "username": email,
            "password": password,
            "grant_type": "password"
        }
        with httpx.Client() as client:
            resp = client.post(url, data=data)
            if resp.status_code == 401:
                raise ValueError("Invalid credentials")
            resp.raise_for_status()
            return resp.json()
