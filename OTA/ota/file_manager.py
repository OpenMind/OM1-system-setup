import logging
import os
import shutil
from typing import Any

import yaml

logging.basicConfig(level=logging.INFO)


class FileManager:
    """Handles file operations for OTA updates."""

    def __init__(self, updates_dir=".ota"):
        """
        Initialize FileManager.

        Parameters
        ----------
        updates_dir : str
            Directory to store OTA updates (default: ".ota")
        """
        self.updates_dir = os.path.abspath(updates_dir)
        os.makedirs(self.updates_dir, mode=0o755, exist_ok=True)

    def store_update_files(
        self, service_name: str, tag: str, temp_yaml_path: str
    ) -> dict:
        """
        Store OTA update files in the updates directory.

        Parameters
        ----------
        service_name : str
            The name of the service
        tag : str
            The update tag/version
        temp_yaml_path : str
            Path to the temporary YAML file to store

        Returns
        -------
        dict
            Result with success status and stored file paths
        """
        try:
            stored_version_yaml_path = os.path.join(
                self.updates_dir, f"{service_name}_{tag}.yaml"
            )
            stored_latest_yaml_path = os.path.join(
                self.updates_dir, f"{service_name}_latest.yaml"
            )

            shutil.copy2(temp_yaml_path, stored_version_yaml_path)
            shutil.copy2(temp_yaml_path, stored_latest_yaml_path)

            logging.info(
                f"Stored OTA update files: {stored_version_yaml_path}, {stored_latest_yaml_path}"
            )

            return {
                "success": True,
                "version_path": stored_version_yaml_path,
                "latest_path": stored_latest_yaml_path,
            }

        except Exception as e:
            error_msg = f"Failed to store OTA update file: {e}"
            logging.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    def load_latest_config(self, service_name: str) -> dict[str, Any]:
        """
        Load the latest configuration for a service.

        Parameters
        ----------
        service_name : str
            The name of the service

        Returns
        -------
        dict
            Result with success status and YAML content or error message
        """
        try:
            stored_latest_yaml_path = os.path.join(
                self.updates_dir, f"{service_name}_latest.yaml"
            )

            if os.path.exists(stored_latest_yaml_path):
                with open(stored_latest_yaml_path, "r") as f:
                    yaml_content = yaml.safe_load(f)
                logging.info(
                    f"Loaded latest configuration from: {stored_latest_yaml_path}"
                )

                return {
                    "success": True,
                    "yaml_content": yaml_content,
                    "file_path": stored_latest_yaml_path,
                }
            else:
                return {
                    "success": False,
                    "error": f"No stored configuration found for service {service_name}",
                }

        except Exception as e:
            error_msg = f"Failed to load latest configuration: {e}"
            logging.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up a temporary file.

        Parameters
        ----------
        file_path : str
            Path to the file to clean up

        Returns
        -------
        bool
            True if cleanup was successful, False otherwise
        """
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logging.info(f"Cleaned up temporary file: {file_path}")
                return True
            return True
        except OSError as e:
            logging.warning(f"Failed to clean up file {file_path}: {e}")
            return False

    def update_env_file(
        self, service_name: str, tag: str, variables: dict[str, str]
    ) -> dict[str, Any]:
        """
        Update environment variables to a service's env file.
        """
        env_file_path = os.path.join(self.updates_dir, f"{service_name}_{tag}.env")

        try:
            existing_vars = self._parse_env_file(env_file_path)
            existing_vars.update(variables)

            with open(env_file_path, "w") as f:
                for key, value in existing_vars.items():
                    f.write(f"{key}={value}\n")

            logging.info(f"Wrote env file for {service_name} {tag}: {env_file_path}")
            return {"success": True, "file_path": env_file_path}
        except Exception as e:
            error_msg = f"Failed to write env file {env_file_path}: {e}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}

    def _parse_env_file(self, path: str) -> dict[str, str]:
        """
        Parse KEY=VALUE lines from an env file.

        Parameters
        ----------
        path : str
            Path to the env file

        Returns
        -------
        dict[str, str]
            Dictionary of environment variables
        """
        result: dict[str, str] = {}
        if not os.path.exists(path):
            return result

        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        result[key] = value
        except Exception as e:
            logging.warning(f"Failed to parse env file {path}: {e}")

        return result

    def read_env_file(self, service_name: str, tag: str) -> dict[str, str]:
        """
        Read env vars from a service's env file.

        Parameters
        ----------
        service_name : str
            The name of the service
        tag : str
            The version tag

        Returns
        -------
        dict[str, str]
            Dictionary of environment variables
        """
        env_file_path = os.path.join(self.updates_dir, f"{service_name}_{tag}.env")
        return self._parse_env_file(env_file_path)
