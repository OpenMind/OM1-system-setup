import json
import logging
from typing import Optional

from ..utils.ws_client import WebSocketClient

logging.basicConfig(level=logging.INFO)


class ProgressReporter:
    """Handles progress reporting for OTA operations."""

    def __init__(self, ws_client: Optional[WebSocketClient] = None):
        """
        Initialize ProgressReporter.

        Parameters
        ----------
        ws_client : WebSocketClient, optional
            WebSocket client for sending progress updates
        """
        self.ws_client = ws_client

    def send_progress_update(self, status: str, message: str, progress: int):
        """
        Send progress update through WebSocket.

        Parameters
        ----------
        status : str
            Current status of the operation
        message : str
            Progress message
        progress : int
            Progress percentage (0-100)
        """
        if self.ws_client and self.ws_client.is_connected():
            update_data = {
                "type": "ota_progress",
                "status": status,
                "message": message,
                "progress": progress,
                "timestamp": json.dumps(None),
            }
            try:
                self.ws_client.send_message(json.dumps(update_data))
                logging.info(
                    f"Sent progress update: {status} - {message} ({progress}%)"
                )
            except Exception as e:
                logging.warning(f"Failed to send progress update: {e}")
        elif self.ws_client:
            logging.warning(
                f"Cannot send progress update - WebSocket not connected: {status} - {message} ({progress}%)"
            )
        else:
            logging.warning(
                f"Cannot send progress update - no WebSocket client: {status} - {message} ({progress}%)"
            )

    def set_ws_client(self, ws_client):
        """
        Set or update the WebSocket client.

        Parameters
        ----------
        ws_client : WebSocketClient
            WebSocket client for sending progress updates
        """
        self.ws_client = ws_client

    def send_env_response(
        self,
        service_name: str,
        variables: list,
        success: bool,
        error: str = "",
    ):
        """
        Send environment variable response.

        Parameters
        ----------
        service_name : str
            Name of the service
        variables : list
            List of environment variable definitions
        success : bool
            Whether the operation was successful
        error : str
            Error message if failed
        """
        if self.ws_client and self.ws_client.is_connected():
            response_data = {
                "type": "env_response",
                "service_name": service_name,
                "variables": variables,
                "success": success,
                "error": error,
            }
            try:
                self.ws_client.send_message(json.dumps(response_data))
                logging.info(f"Sent env_response for {service_name}: success={success}")
            except Exception as e:
                logging.warning(f"Failed to send env_response: {e}")
        else:
            logging.warning("WebSocket not connected")
