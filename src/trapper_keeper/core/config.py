"""Configuration management for Trapper Keeper MCP."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json
import yaml
from dotenv import load_dotenv
from pydantic import ValidationError
import structlog

from .types import TrapperKeeperConfig

logger = structlog.get_logger()


class ConfigManager:
    """Manages configuration for Trapper Keeper."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config: Optional[TrapperKeeperConfig] = None
        self._logger = logger.bind(component="ConfigManager")
        
        # Load environment variables
        load_dotenv()
        
    def load(self) -> TrapperKeeperConfig:
        """Load configuration from file or environment."""
        if self._config is not None:
            return self._config
            
        config_data = {}
        
        # Try to load from file
        if self.config_path and self.config_path.exists():
            config_data = self._load_from_file(self.config_path)
            
        # Override with environment variables
        config_data = self._merge_with_env(config_data)
        
        # Create and validate config
        try:
            self._config = TrapperKeeperConfig(**config_data)
            self._logger.info("configuration_loaded", source=str(self.config_path))
        except ValidationError as e:
            self._logger.error("configuration_validation_failed", errors=e.errors())
            raise
            
        return self._config
        
    def save(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if self._config is None:
            raise RuntimeError("No configuration loaded")
            
        save_path = path or self.config_path
        if save_path is None:
            raise ValueError("No path specified for saving configuration")
            
        # Determine format from extension
        if save_path.suffix == ".yaml" or save_path.suffix == ".yml":
            content = yaml.safe_dump(self._config.model_dump(), default_flow_style=False)
        else:
            content = json.dumps(self._config.model_dump(), indent=2)
            
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(content)
        self._logger.info("configuration_saved", path=str(save_path))
        
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if self._config is None:
            self.load()
            
        # Update config with new values
        config_data = self._config.model_dump()
        self._deep_update(config_data, updates)
        
        # Recreate config to validate
        try:
            self._config = TrapperKeeperConfig(**config_data)
            self._logger.info("configuration_updated", updates=updates)
        except ValidationError as e:
            self._logger.error("configuration_update_failed", errors=e.errors())
            raise
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key."""
        if self._config is None:
            self.load()
            
        parts = key.split(".")
        value = self._config.model_dump()
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
                
        return value
        
    def _load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not path.exists():
            return {}
            
        content = path.read_text()
        
        if path.suffix == ".yaml" or path.suffix == ".yml":
            return yaml.safe_load(content) or {}
        elif path.suffix == ".json":
            return json.loads(content)
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content) or {}
                
    def _merge_with_env(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration with environment variables."""
        # Environment variable mapping
        env_mapping = {
            "TRAPPER_KEEPER_LOG_LEVEL": "log_level",
            "TRAPPER_KEEPER_METRICS_PORT": "metrics_port",
            "TRAPPER_KEEPER_MCP_PORT": "mcp_port",
            "TRAPPER_KEEPER_MCP_HOST": "mcp_host",
            "TRAPPER_KEEPER_OUTPUT_DIR": "organization.output_dir",
            "TRAPPER_KEEPER_MAX_CONCURRENT": "max_concurrent_processing",
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Handle nested keys
                if "." in config_key:
                    parts = config_key.split(".")
                    current = config_data
                    
                    # Create nested structure if needed
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                        
                    # Set the value
                    last_part = parts[-1]
                    if last_part == "output_dir":
                        current[last_part] = Path(value)
                    elif last_part in ["metrics_port", "mcp_port", "max_concurrent_processing"]:
                        current[last_part] = int(value)
                    else:
                        current[last_part] = value
                else:
                    # Simple key
                    if config_key == "output_dir":
                        config_data[config_key] = Path(value)
                    elif config_key in ["metrics_port", "mcp_port", "max_concurrent_processing"]:
                        config_data[config_key] = int(value)
                    else:
                        config_data[config_key] = value
                        
        return config_data
        
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep update a dictionary."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Path] = None) -> ConfigManager:
    """Get or create the global config manager."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
        
    return _config_manager


def get_config() -> TrapperKeeperConfig:
    """Get the current configuration."""
    return get_config_manager().load()