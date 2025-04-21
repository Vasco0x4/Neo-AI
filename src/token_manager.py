import httpx
import jwt
import json
import os
import logging
import tempfile

logging.disable(logging.CRITICAL)  # Disable logging

class TokenManager:
    def __init__(self, agent_id, agent_key, auth_api_url):
        self.agent_id = agent_id
        self.agent_key = agent_key
        self.auth_api_url = auth_api_url

        self.cache_file = os.path.join(tempfile.gettempdir(), "token_cache.json")
        logging.basicConfig(level=logging.INFO)

    def _request(self, method, endpoint, headers=None, params=None, data=None):
        try:
            url = f"{self.auth_api_url}{endpoint}"
            # Using httpx.request directly instead of creating a client
            # This method helps bypass proxy usage
            response = httpx.request(method, url, headers=headers, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logging.error(f"Request failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error {response.status_code}: {response.text}")
            raise

    def _get_refresh_token(self):
        logging.info("Requesting refresh token...")
        response = self._request(
            "POST",
            f"/auth/agents/{self.agent_id}/token",
            headers={"Content-Type": "application/json", "X-Api-Key": self.agent_key},
        )
        return response["refresh_token"]

    def _get_access_token(self, refresh_token):
        logging.info("Requesting access token using refresh token...")
        response = self._request(
            "PUT",
            f"/auth/agents/{self.agent_id}/token",
            headers={"Content-Type": "application/json", "X-Api-Key": self.agent_key},
            params={"refresh_token": refresh_token},
        )
        return response["access_token"]

    def _is_token_expired(self, token):
        try:
            jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
            return False
        except jwt.ExpiredSignatureError:
            logging.info("Token has expired.")
            return True
        except Exception as e:
            logging.error(f"Error while validating token: {e}")
            return True

    def _load_tokens_from_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    tokens = json.load(f)
                    if self._is_token_expired(tokens.get("access_token")) and self._is_token_expired(
                            tokens.get("refresh_token")):
                        logging.warning("Both access and refresh tokens are expired. Clearing cache.")
                        os.remove(self.cache_file)
                        return None
                    return tokens
            except json.JSONDecodeError:
                logging.warning("Cache file is corrupted. Ignoring it.")
        return None

    def _save_tokens_to_cache(self, access_token, refresh_token):
        with open(self.cache_file, "w") as f:
            json.dump({"access_token": access_token, "refresh_token": refresh_token}, f)

    def get_valid_access_token(self):
        try:
            tokens = self._load_tokens_from_cache()

            if tokens and not self._is_token_expired(tokens["access_token"]):
                logging.info("Using valid cached access token.")
                return tokens["access_token"]

            if tokens and not self._is_token_expired(tokens["refresh_token"]):
                logging.info("Cached access token expired. Refreshing...")
                refresh_token = tokens["refresh_token"]
            else:
                logging.info("No valid refresh token found. Requesting a new one...")
                refresh_token = self._get_refresh_token()

            access_token = self._get_access_token(refresh_token)
            self._save_tokens_to_cache(access_token, refresh_token)
            return access_token

        except Exception as e:
            logging.error(f"Failed to get a valid access token: {e}")
            raise