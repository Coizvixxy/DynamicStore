from django.conf import settings
import importlib
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, object] = {}
        self.plugin_states: Dict[str, bool] = {}  # Store plugin enabled/disabled states
        
    def discover_plugins(self) -> None:
        """Discover and load all available plugins"""
        plugins_dir = os.path.join(settings.BASE_DIR, 'plugins')
        loaded_count = 0
        
        for item in os.listdir(plugins_dir):
            if os.path.isdir(os.path.join(plugins_dir, item)) and not item.startswith('_'):
                try:
                    module = importlib.import_module(f'plugins.{item}.plugin')
                    plugin = module.Plugin()
                    self.plugins[item] = plugin
                    self.plugin_states[item] = True  # Default to enabled
                    plugin.initialize()
                    loaded_count += 1
                    logger.info(f"Successfully loaded plugin: {plugin.name} v{plugin.version}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {item}: {str(e)}")
        
        logger.info(f"Loaded {loaded_count} plugins")
    
    def get_plugin(self, name: str) -> Optional[object]:
        """Get a specific plugin by name"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[tuple]:
        """Get all plugins with their states"""
        return [(name, plugin, self.plugin_states.get(name, False)) 
                for name, plugin in self.plugins.items()]
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a specific plugin"""
        if name in self.plugins:
            try:
                self.plugins[name].initialize()
                self.plugin_states[name] = True
                logger.info(f"Enabled plugin: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to enable plugin {name}: {str(e)}")
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a specific plugin"""
        if name in self.plugins:
            try:
                self.plugins[name].cleanup()
                self.plugin_states[name] = False
                logger.info(f"Disabled plugin: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to disable plugin {name}: {str(e)}")
        return False
    
    def get_urls(self):
        """Get all URLs from enabled plugins"""
        urls = []
        for name, plugin in self.plugins.items():
            if self.plugin_states.get(name, False):
                if hasattr(plugin, 'get_urls'):
                    urls.extend(plugin.get_urls())
        return urls

plugin_manager = PluginManager()