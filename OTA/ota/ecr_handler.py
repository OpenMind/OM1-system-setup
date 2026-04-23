import logging
import os

import requests

from .docker_operations import DockerManager
from .progress_reporter import ProgressReporter

logging.basicConfig(level=logging.INFO)

ECR_CREDENTIALS_URL = os.getenv(
    "ECR_CREDENTIALS_URL", "https://api.openmind.com/api/core/v1/ota/ecr/credentials"
)
OM_API_KEY = os.getenv("OM_API_KEY")


class ECRHandler:
    """Handles ECR credential requests and docker login for private images."""

    def __init__(
        self,
        docker_manager: DockerManager,
        progress_reporter: ProgressReporter,
    ):
        self.docker_manager = docker_manager
        self.progress_reporter = progress_reporter

    def is_private_ecr(self, yaml_content: dict) -> str | None:
        """Return ECR repo name if any service uses a private ECR image, else None."""
        for svc in yaml_content.get("services", {}).values():
            image = svc.get("image", "")
            if ".dkr.ecr." in image:
                repo = image
                slash_idx = repo.find("/")
                if slash_idx > 0 and "." in repo[:slash_idx]:
                    repo = repo[slash_idx + 1 :]
                colon_idx = repo.find(":")
                if colon_idx > 0:
                    repo = repo[:colon_idx]
                return repo
        return None

    def login_if_needed(self, yaml_content: dict) -> bool:
        """Check for private ECR image and login if needed. Returns True on success or no ECR."""
        ecr_image = self.is_private_ecr(yaml_content)
        if not ecr_image:
            return True
        return self._fetch_credentials_and_login(ecr_image)

    def _fetch_credentials_and_login(self, image: str) -> bool:
        """Fetch ECR credentials via HTTP and perform docker login."""
        if not ECR_CREDENTIALS_URL or not OM_API_KEY:
            logging.error("ECR_CREDENTIALS_URL or OM_API_KEY not configured")
            self.progress_reporter.send_progress_update(
                "error", "ECR credentials endpoint not configured", 15
            )
            return False

        self.progress_reporter.send_progress_update(
            "authenticating", "Requesting ECR credentials", 15
        )

        try:
            resp = requests.post(
                ECR_CREDENTIALS_URL,
                headers={
                    "x-api-key": OM_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"image": image},
                timeout=30,
            )
        except requests.RequestException as e:
            logging.error(f"ECR credentials request failed: {e}")
            self.progress_reporter.send_progress_update(
                "error", f"ECR credentials request failed: {e}", 15
            )
            return False

        if not resp.ok:
            error_detail = (
                resp.json().get("error", resp.text) if resp.text else "unknown"
            )
            logging.error(f"ECR credentials error ({resp.status_code}): {error_detail}")
            self.progress_reporter.send_progress_update(
                "error", f"ECR credentials error: {error_detail}", 15
            )
            return False

        creds = resp.json()

        login_ok = self.docker_manager.login_docker_ecr(
            registry=creds.get("registry", ""),
            username=creds.get("username", ""),
            password=creds.get("password", ""),
        )
        if not login_ok:
            logging.error("Docker ECR login failed")
            self.progress_reporter.send_progress_update(
                "error", "Docker ECR login failed", 15
            )
            return False

        logging.info(f"ECR login succeeded, expires at {creds.get('expires_at')}")
        return True
