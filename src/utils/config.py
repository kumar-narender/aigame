"""Configuration management for the application"""

import json
import os
from typing import Dict, Any, Optional


class Config:
    """
    Configuration manager for the application.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to configuration file (JSON format)
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = self._load_default_config()

        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "scraper": {
                "timeout": 30,
                "max_retries": 3,
                "user_agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"
            },
            "newsletter": {
                "template_style": "html",
                "max_items": 10,
                "include_images": False
            },
            "output": {
                "directory": "output",
                "filename_template": "newsletter_{date}.{ext}"
            }
        }

    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from a JSON file.

        Args:
            config_file: Path to configuration file
        """
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
            print(f"Configuration loaded from {config_file}")
        except Exception as e:
            print(f"Error loading configuration file: {e}")

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration with existing configuration.

        Args:
            new_config: New configuration dictionary
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'scraper.timeout')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save_to_file(self, config_file: Optional[str] = None) -> None:
        """
        Save configuration to a JSON file.

        Args:
            config_file: Path to save configuration (uses self.config_file if not provided)
        """
        output_file = config_file or self.config_file

        if not output_file:
            raise ValueError("No configuration file specified")

        try:
            with open(output_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {output_file}")
        except Exception as e:
            print(f"Error saving configuration file: {e}")

    def get_scraper_config(self) -> Dict[str, Any]:
        """
        Get scraper-specific configuration.

        Returns:
            Scraper configuration dictionary
        """
        return self.config.get("scraper", {})

    def get_newsletter_config(self) -> Dict[str, Any]:
        """
        Get newsletter-specific configuration.

        Returns:
            Newsletter configuration dictionary
        """
        return self.config.get("newsletter", {})

    def __repr__(self) -> str:
        return f"Config(file='{self.config_file}')"
