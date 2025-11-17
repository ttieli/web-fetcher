"""
Configuration Loader for Routing System

Handles loading, validating, and caching routing configuration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not available - validation disabled")

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class ConfigLoader:
    """
    Loads and validates routing configuration from YAML file.

    Attributes:
        config_path: Path to routing.yaml
        schema_path: Path to routing_schema.json
        _config: Cached configuration dict
        _schema: Cached schema dict
    """

    def __init__(self, config_path: Optional[str] = None, schema_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to routing.yaml (optional, uses default if not provided)
            schema_path: Path to routing_schema.json (optional)
        """
        # Default paths
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "routing.yaml"

        if schema_path is None:
            project_root = Path(__file__).parent.parent
            schema_path = project_root / "config" / "routing_schema.json"

        self.config_path = Path(config_path)
        self.schema_path = Path(schema_path)

        self._config: Optional[Dict[str, Any]] = None
        self._schema: Optional[Dict[str, Any]] = None

    def load(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            force_reload: If True, bypass cache and reload from disk

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If configuration file is missing or invalid
        """
        # Return cached config if available
        if self._config is not None and not force_reload:
            return self._config

        # Check if config file exists
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create config/routing.yaml"
            )

        try:
            # Load YAML
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                raise ConfigurationError("Configuration file is empty")

            logger.info(f"Loaded configuration from: {self.config_path}")

            # Validate against schema
            if JSONSCHEMA_AVAILABLE:
                self._validate(config)
            else:
                logger.warning("jsonschema not available - skipping validation")

            # Cache and return
            self._config = config
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _validate(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration against JSON schema.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigurationError: If validation fails
        """
        if not JSONSCHEMA_AVAILABLE:
            return

        # Load schema if not cached
        if self._schema is None:
            if not self.schema_path.exists():
                logger.warning(f"Schema file not found: {self.schema_path}, skipping validation")
                return

            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self._schema = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load schema: {e}, skipping validation")
                return

        # Validate
        try:
            jsonschema.validate(instance=config, schema=self._schema)
            logger.info("✓ Configuration validation passed")
        except jsonschema.ValidationError as e:
            raise ConfigurationError(
                f"Configuration validation failed:\n"
                f"  Path: {' -> '.join(str(p) for p in e.path)}\n"
                f"  Error: {e.message}"
            )
        except jsonschema.SchemaError as e:
            raise ConfigurationError(f"Invalid schema: {e.message}")

    def get_version(self) -> str:
        """Get configuration version."""
        config = self.load()
        return config.get('version', 'unknown')

    def get_global_settings(self) -> Dict[str, Any]:
        """Get global settings from configuration."""
        config = self.load()
        return config.get('global', {})

    def get_rules(self) -> list:
        """Get routing rules from configuration."""
        config = self.load()
        rules = config.get('rules', [])

        # Sort by priority (descending)
        return sorted(rules, key=lambda r: r.get('priority', 0), reverse=True)

    def reload(self) -> Dict[str, Any]:
        """Force reload configuration from disk."""
        return self.load(force_reload=True)
