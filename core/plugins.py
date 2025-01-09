from abc import ABC, abstractmethod
import importlib
import os
import logging
from typing import Dict, List, Optional, Type
from django.conf import settings

logger = logging.getLogger(__name__)

class PluginInterface(ABC):
    """Abstract base class that all plugins must implement"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin's name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the plugin's version"""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup when plugin is disabled"""
        pass

class PluginManager:
    """Manages the loading and lifecycle of plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_dir = getattr(settings, 'PLUGIN_DIR', 'plugins')
        
    def discover_plugins(self) -> None:
        """Scan plugin directory and load available plugins"""
        plugin_path = os.path.join(os.path.dirname(__file__), self._plugin_dir)
        
        try:
            for item in os.listdir(plugin_path):
                if os.path.isdir(os.path.join(plugin_path, item)) and not item.startswith('_'):
                    self._load_plugin(item)
        except FileNotFoundError:
            logger.warning(f"Plugin directory {plugin_path} not found")
    
    def _load_plugin(self, plugin_name: str) -> None:
        """Load a single plugin by name"""
        try:
            # Import the plugin module
            module = importlib.import_module(f"{self._plugin_dir}.{plugin_name}.plugin")
            
            # Get the plugin class (should be named Plugin)
            plugin_class: Type[PluginInterface] = getattr(module, 'Plugin')
            
            # Instantiate and initialize the plugin
            plugin = plugin_class()
            plugin.initialize()
            
            # Store the plugin instance
            self._plugins[plugin.name] = plugin
            logger.info(f"Successfully loaded plugin: {plugin.name} v{plugin.version}")
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin instance by name"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[PluginInterface]:
        """Get all loaded plugin instances"""
        return list(self._plugins.values())
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin by name"""
        plugin = self.get_plugin(name)
        if plugin:
            try:
                plugin.initialize()
                return True
            except Exception as e:
                logger.error(f"Failed to enable plugin {name}: {str(e)}")
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin by name"""
        plugin = self.get_plugin(name)
        if plugin:
            try:
                plugin.cleanup()
                return True
            except Exception as e:
                logger.error(f"Failed to disable plugin {name}: {str(e)}")
        return False

# Global plugin manager instance
plugin_manager = PluginManager()