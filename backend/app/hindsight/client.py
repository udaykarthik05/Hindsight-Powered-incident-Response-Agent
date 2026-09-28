import asyncio
from typing import Optional
from pydantic import BaseModel
from hindsight_client import Hindsight

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("hindsight.client")


class HindsightConnectionStatus(BaseModel):
    """Model representing the connectivity status of Hindsight."""
    connected: bool
    base_url: str
    bank_id: str
    server_version: Optional[str] = None
    error: Optional[str] = None
    message: str


class HindsightClientManager:
    """Manages the official Hindsight client instance and lifecycle."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client: Optional[Hindsight] = None

    def get_client(self) -> Hindsight:
        """Get or initialize the Hindsight client."""
        if self._client is None:
            logger.info(
                "Initializing Hindsight client pointing to: %s",
                self.settings.hindsight_base_url,
            )
            self._client = Hindsight(
                base_url=self.settings.hindsight_base_url,
                api_key=self.settings.hindsight_api_key or None,
                timeout=self.settings.hindsight_timeout,
            )
        return self._client

    async def check_connection(self) -> HindsightConnectionStatus:
        """
        Verify connectivity to the Hindsight server without faking success.
        
        Attempts to call the server's version endpoint. If unreachable or unauthenticated,
        returns an honest status report detailing the issue.
        """
        client = self.get_client()
        try:
            # Query server version asynchronously
            version_response = await client.aget_version()
            version_str = getattr(version_response, "version", str(version_response))
            logger.info("Successfully connected to Hindsight server (version: %s)", version_str)
            return HindsightConnectionStatus(
                connected=True,
                base_url=self.settings.hindsight_base_url,
                bank_id=self.settings.hindsight_bank_id,
                server_version=str(version_str),
                message="Connected to Hindsight memory service successfully.",
            )
        except (TimeoutError, asyncio.TimeoutError) as err:
            err_msg = f"Connection timed out after {self.settings.hindsight_timeout}s"
            logger.warning("Hindsight connection timeout at %s: %s", self.settings.hindsight_base_url, err)
            return HindsightConnectionStatus(
                connected=False,
                base_url=self.settings.hindsight_base_url,
                bank_id=self.settings.hindsight_bank_id,
                error=err_msg,
                message=(
                    "Hindsight server is unreachable (timed out). "
                    "Ensure the Hindsight server is running or check HINDSIGHT_BASE_URL."
                ),
            )
        except Exception as err:
            err_msg = f"{type(err).__name__}: {str(err)}"
            logger.warning("Failed to connect to Hindsight at %s: %s", self.settings.hindsight_base_url, err_msg)
            return HindsightConnectionStatus(
                connected=False,
                base_url=self.settings.hindsight_base_url,
                bank_id=self.settings.hindsight_bank_id,
                error=err_msg,
                message=(
                    "Could not establish connection to Hindsight. "
                    "Verify the server is running and HINDSIGHT_BASE_URL / HINDSIGHT_API_KEY are properly configured."
                ),
            )

    async def close(self) -> None:
        """Close client sessions cleanly to avoid resource leaks."""
        if self._client is not None:
            try:
                await self._client.aclose()
                logger.info("Hindsight client session closed.")
            except Exception as err:
                logger.warning("Error while closing Hindsight client: %s", err)
            finally:
                self._client = None


# Global singleton manager instance
_client_manager: Optional[HindsightClientManager] = None


def get_hindsight_manager() -> HindsightClientManager:
    """Return the global HindsightClientManager instance."""
    global _client_manager
    if _client_manager is None:
        _client_manager = HindsightClientManager()
    return _client_manager
