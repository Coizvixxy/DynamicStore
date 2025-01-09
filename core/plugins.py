from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from django.urls import path
import importlib
import os
import logging
from django.conf import settings
import json

logger = logging.getLogger('core.plugins')

class PluginInterface(ABC):
    """Base interface that all plugins must implement"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """List of required plugin names"""
        return []
    
    @property
    def conflicts(self) -> List[str]:
        """List of conflicting plugin names"""
        return []
    
    def get_urls(self):
        """Return a list of URLs for the plugin"""
        return []
    
    def initialize(self) -> None:
        """Called when plugin is loaded"""
        pass
    
    def cleanup(self) -> None:
        """Called when plugin is unloaded"""
        pass

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, object] = {}
        self.plugin_states: Dict[str, bool] = {}
        self._load_plugin_states()
        logger.info("Plugin manager initialized")
    
    def _load_plugin_states(self):
        """Load plugin states from configuration file"""
        try:
            with open('plugin_config.json', 'r') as f:
                self.plugin_states = json.load(f)
        except FileNotFoundError:
            self.plugin_states = {}
    
    def _save_plugin_states(self):
        """Save plugin states to configuration file"""
        with open('plugin_config.json', 'w') as f:
            json.dump(self.plugin_states, f)
    
    def check_dependencies(self, plugin_name: str) -> bool:
        """Check if all dependencies are satisfied"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
            
        for dep in plugin.dependencies:
            if dep not in self.plugins or not self.plugin_states.get(dep, False):
                logger.warning(f"Plugin {plugin_name} requires {dep} to be enabled")
                return False
        return True
    
    def check_conflicts(self, plugin_name: str) -> bool:
        """Check for conflicts with other enabled plugins"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return False
            
        for conflict in plugin.conflicts:
            if conflict in self.plugins and self.plugin_states.get(conflict, False):
                logger.warning(f"Plugin {plugin_name} conflicts with enabled plugin {conflict}")
                return False
        return True
    
    def discover_plugins(self) -> None:
        """Discover and load all plugins"""
        plugins_dir = os.path.join(settings.BASE_DIR, 'plugins')
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            logger.info(f"Created plugins directory at {plugins_dir}")
            return
        
        logger.info(f"Scanning for plugins in: {plugins_dir}")
        
        # 首先加載所有插件類
        for item in os.listdir(plugins_dir):
            if os.path.isdir(os.path.join(plugins_dir, item)) and not item.startswith('_'):
                try:
                    module = importlib.import_module(f'plugins.{item}.plugin')
                    plugin = module.Plugin()
                    self.plugins[item] = plugin
                    # 默認啟用 server_logs 插件
                    if item == 'server_logs':
                        self.plugin_states[item] = True
                    logger.info(f"Found plugin: {item} (version: {plugin.version})")
                except Exception as e:
                    logger.error(f"Failed to load plugin {item}: {str(e)}")
        
        # 初始化已啟用的插件
        for name, enabled in self.plugin_states.items():
            if enabled and name in self.plugins:
                if self.check_dependencies(name) and self.check_conflicts(name):
                    try:
                        self.plugins[name].initialize()
                        logger.info(f"Initialized plugin: {name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize plugin {name}: {str(e)}")
                        self.plugin_states[name] = False
                else:
                    self.plugin_states[name] = False
        
        self._save_plugin_states()
    
    def get_urls(self):
        """Get all URLs from enabled plugins"""
        urls = []
        for name, plugin in self.plugins.items():
            if self.plugin_states.get(name, False):
                if hasattr(plugin, 'get_urls'):
                    try:
                        plugin_urls = plugin.get_urls()
                        urls.extend(plugin_urls)
                        logger.info(f"Added URLs from plugin {name}: {[url.pattern for url in plugin_urls]}")
                    except Exception as e:
                        logger.error(f"Error getting URLs from plugin {name}: {str(e)}")
        return urls
    
    def get_plugin_info(self, name: str) -> dict:
        """Get detailed information about a plugin"""
        plugin = self.plugins.get(name)
        if not plugin:
            return {}
            
        return {
            'name': plugin.name,
            'version': plugin.version,
            'enabled': self.plugin_states.get(name, False),
            'description': plugin.__doc__ or "No description available",
            'dependencies': plugin.dependencies,
            'conflicts': plugin.conflicts,
            'can_enable': self.check_dependencies(name) and self.check_conflicts(name),
            'urls': [url.pattern for url in plugin.get_urls()] if hasattr(plugin, 'get_urls') else []
        }
    
    def get_all_plugins(self) -> List[dict]:
        """Get information about all plugins"""
        return [self.get_plugin_info(name) for name in self.plugins.keys()]
    
    def get_plugin(self, name: str) -> Optional[object]:
        """Get a specific plugin by name"""
        plugin = self.plugins.get(name)
        if plugin and self.plugin_states.get(name, False):
            return plugin
        logger.warning(f"Plugin not found or not enabled: {name}")
        return None

plugin_manager = PluginManager()