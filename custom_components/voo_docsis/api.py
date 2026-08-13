"""Asynchronous API client for Technicolor VOO Cable Modem (CGA4233VOO)."""
import asyncio
import binascii
import hashlib
import http.cookiejar
import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Exception raised when connection to modem fails."""


class InvalidAuth(Exception):
    """Exception raised when authentication with modem fails."""


def calculate_pbkdf2_hex(password: str, salt: str, count: int = 1000, dklen: int = 16) -> str:
    """Calculate PBKDF2 HMAC-SHA256 hex string matching Technicolor modem's SJCL implementation."""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        count,
        dklen
    )
    return binascii.hexlify(key).decode('utf-8')


class VooTechnicolorApi:
    """API Client for Technicolor VOO DOCSIS Router."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: Optional[Any] = None
    ) -> None:
        """Initialize the API client."""
        self.host = host.rstrip('/')
        if not self.host.startswith("http://") and not self.host.startswith("https://"):
            self.base_url = f"http://{self.host}"
        else:
            self.base_url = self.host

        self.username = username.strip().lower()  # Technicolor backend requires lowercase username (e.g. 'voo')
        self.password = password
        self._auth_token: str = ""
        self._cj = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))

    async def close(self) -> None:
        """Close session resources."""
        pass

    async def async_authenticate(self) -> bool:
        """Authenticate with the modem using the two-stage PBKDF2 challenge in thread pool."""
        return await asyncio.to_thread(self._sync_authenticate)

    def _sync_authenticate(self) -> bool:
        """Authenticate using urllib with isolated cookie jar."""
        login_url = f"{self.base_url}/api/v1/session/login"
        self._cj.clear()

        # Step 1: seek salt
        data1 = urllib.parse.urlencode({"username": self.username, "password": "seeksalthash"}).encode('utf-8')
        req1 = urllib.request.Request(
            login_url,
            data=data1,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/"
            }
        )

        try:
            with self._opener.open(req1, timeout=10) as resp:
                res1 = json.loads(resp.read().decode('utf-8'))
        except Exception as err:
            raise CannotConnect(f"Failed to connect to modem at {self.base_url}: {err}") from err

        if res1.get("error") != "ok":
            raise InvalidAuth(f"Step 1 login failed for user '{self.username}': {res1.get('message')}")

        salt = res1.get("salt")
        saltwebui = res1.get("saltwebui")

        if salt == "none":
            final_password = self.password
        else:
            hashed1 = calculate_pbkdf2_hex(self.password, salt)
            final_password = calculate_pbkdf2_hex(hashed1, saltwebui)

        # Step 2: final login (No X-CSRF-TOKEN header during login)
        data2 = urllib.parse.urlencode({"username": self.username, "password": final_password}).encode('utf-8')
        headers2 = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/"
        }

        req2 = urllib.request.Request(login_url, data=data2, headers=headers2)
        try:
            with self._opener.open(req2, timeout=10) as resp2:
                res2 = json.loads(resp2.read().decode('utf-8'))
        except Exception as err:
            raise CannotConnect(f"Failed to complete login on step 2: {err}") from err

        if res2.get("error") != "ok":
            raise InvalidAuth(f"Invalid credentials for user '{self.username}'")

        cookies = {c.name: c.value for c in self._cj}
        if "auth" in cookies:
            self._auth_token = cookies["auth"]
        _LOGGER.debug("Successfully authenticated with VOO modem at %s", self.base_url)
        return True

    async def _async_request(self, endpoint: str, retry_auth: bool = True) -> Dict[str, Any]:
        """Make an authenticated GET request to a modem API endpoint in thread pool."""
        return await asyncio.to_thread(self._sync_request, endpoint, retry_auth)

    def _sync_request(self, endpoint: str, retry_auth: bool = True) -> Dict[str, Any]:
        """Request endpoint using urllib."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cookies = {c.name: c.value for c in self._cj}
        auth_token = cookies.get("auth", self._auth_token)

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.base_url}/"
        }
        if auth_token:
            headers["X-CSRF-TOKEN"] = auth_token

        req = urllib.request.Request(url, headers=headers)
        try:
            with self._opener.open(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            if err.code == 401 and retry_auth:
                _LOGGER.debug("Session expired (401), re-authenticating...")
                self._sync_authenticate()
                return self._sync_request(endpoint, retry_auth=False)
            raise CannotConnect(f"HTTP Error {err.code} on endpoint {endpoint}") from err
        except Exception as err:
            raise CannotConnect(f"Error requesting {endpoint}: {err}") from err

    async def async_get_all_data(self) -> Dict[str, Any]:
        """Fetch menu, modem DOCSIS metrics, and system information."""
        try:
            await self._async_request("api/v1/session/menu")
        except InvalidAuth:
            await self.async_authenticate()
            await self._async_request("api/v1/session/menu")

        modem_resp = await self._async_request("api/v1/modem")
        system_resp = await self._async_request("api/v1/system")

        return {
            "modem": modem_resp.get("data", {}),
            "system": system_resp.get("data", {})
        }
