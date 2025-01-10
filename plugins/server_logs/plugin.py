from core.plugins import PluginInterface
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import os
from datetime import datetime
import re
import importlib
import logging

logger = logging.getLogger(__name__)

class Plugin(PluginInterface):
    """Monitor and display Django server logs, terminal output, and user activities in real-time"""
    
    REQUIRED_PACKAGES = ['psutil']
    
    def __init__(self):
        self.check_dependencies()
        self.psutil = importlib.import_module('psutil')
    
    def check_dependencies(self):
        """檢查必要的依賴包是否已安裝"""
        missing_packages = []
        for package in self.REQUIRED_PACKAGES:
            try:
                importlib.import_module(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            raise ImportError(
                f"Missing required packages for Server Logs plugin: {', '.join(missing_packages)}. "
                f"Please install them using: pip install {' '.join(missing_packages)}"
            )
    
    LOG_TYPES = {
        'server': 'Server Logs',
        'activity': 'User Activity',
        'terminal': 'Terminal Output',
        'messages': 'System Messages',
        'django': 'Django Server'
    }
    
    @property
    def name(self) -> str:
        return "Server Logs"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_urls(self):
        """Return a list of URLs for the plugin"""
        return [
            path('logs/', self.view_logs, name='server_logs'),  # 默認視圖
            path('logs/<str:log_type>/', self.view_logs, name='view_logs'),
            path('logs/<str:log_type>/api/', self.get_logs_api, name='get_logs'),
            path('logs/message/add/', self.add_message, name='add_log_message'),
        ]
    
    def is_superuser(self, user):
        """檢查用戶是否是超級用戶"""
        return user.is_superuser
    
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def view_logs(self, request, log_type='server'):
        """渲染日誌視圖"""
        context = {
            'log_type': log_type,
            'log_types': self.LOG_TYPES,
            'plugin_logs': self.read_plugin_logs(),  # 添加插件日誌
        }
        return render(request, 'server_logs/logs_content.html', context)
    
    def get_logs_api(self, request, log_type):
        """API endpoint for fetching logs"""
        try:
            if not request.user.is_superuser:
                logger.warning(f"Unauthorized access attempt from {request.user}")
                return JsonResponse({
                    'error': 'Permission denied'
                }, status=403)

            n = int(request.GET.get('lines', 100))
            logger.debug(f"Fetching {n} lines of {log_type} logs")
            
            logs = []
            if log_type == 'server':
                logs = self.read_server_logs(n)
            elif log_type == 'activity':
                logs = self.read_activity_logs(n)
            elif log_type == 'terminal':
                logs = self.read_terminal_logs(n)
            elif log_type == 'messages':
                logs = self.read_message_logs(n)
            else:
                logger.error(f"Unknown log type requested: {log_type}")
                return JsonResponse({
                    'error': f'Unknown log type: {log_type}'
                }, status=400)
            
            logger.debug(f"Retrieved {len(logs)} log entries")
            return JsonResponse({
                'logs': logs,
                'timestamp': datetime.now().isoformat(),
                'count': len(logs)
            })
        except Exception as e:
            logger.error(f"Error in get_logs_api: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f"Failed to fetch logs: {str(e)}"
            }, status=500)
    
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def add_message(self, request):
        """Add a new system message"""
        if request.method == 'POST':
            level = request.POST.get('level', 'INFO')
            message = request.POST.get('message', '')
            
            with open('messages.log', 'a') as f:
                timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
                f.write(f'[{timestamp}] {level}: {message}\n')
            
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=400)
    
    def read_server_logs(self, n_lines=100):
        """Read server logs"""
        try:
            with open('server.log', 'r') as f:
                lines = f.readlines()[-n_lines:]
                return [{
                    'timestamp': line.split(']')[0].strip('['),
                    'level': line.split(']')[1].split(':')[0].strip(),
                    'message': ':'.join(line.split(':')[1:]).strip()
                } for line in lines]
        except FileNotFoundError:
            return [{
                'timestamp': datetime.now().strftime('%d/%b/%Y %H:%M:%S'),
                'level': 'ERROR',
                'message': 'Server log file not found'
            }]
    
    def read_activity_logs(self, n_lines=100):
        """Read activity logs"""
        try:
            with open('activity.log', 'r') as f:
                lines = f.readlines()[-n_lines:]
                return [{
                    'timestamp': line.split(']')[0].strip('['),
                    'level': line.split(']')[1].split(':')[0].strip(),
                    'message': ':'.join(line.split(':')[1:]).strip()
                } for line in lines]
        except FileNotFoundError:
            return [{
                'timestamp': datetime.now().strftime('%d/%b/%Y %H:%M:%S'),
                'level': 'ERROR',
                'message': 'Activity log file not found'
            }]
    
    def read_terminal_logs(self, n_lines=100):
        """Read terminal output"""
        try:
            with open('terminal.log', 'r') as f:
                return self.parse_logs(f.readlines()[-n_lines:])
        except FileNotFoundError:
            return [{
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'message': 'Terminal log file not found'
            }]
    
    def read_message_logs(self, n_lines=100):
        """Read system messages"""
        try:
            with open('messages.log', 'r') as f:
                return self.parse_logs(f.readlines()[-n_lines:])
        except FileNotFoundError:
            return [{
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'message': 'Messages log file not found'
            }]
    
    def parse_logs(self, log_lines):
        """Parse log lines into structured data"""
        parsed_logs = []
        
        for line in log_lines:
            try:
                match = re.match(r'\[(.*?)\] (\w+): (.*)', line.strip())
                if match:
                    timestamp, level, message = match.groups()
                    parsed_logs.append({
                        'timestamp': timestamp,
                        'level': level,
                        'message': message
                    })
                else:
                    parsed_logs.append({
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'message': line.strip()
                    })
            except Exception as e:
                parsed_logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR',
                    'message': f'Error parsing log line: {str(e)}'
                })
        
        return parsed_logs 
    
    def initialize(self):
        """Initialize plugin and create log files if they don't exist"""
        log_files = ['server.log', 'activity.log', 'terminal.log', 'messages.log']
        for log_file in log_files:
            if not os.path.exists(log_file):
                try:
                    with open(log_file, 'w') as f:
                        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
                        f.write(f'[{timestamp}] INFO: {log_file} initialized\n')
                except Exception as e:
                    logger.error(f"Failed to create {log_file}: {str(e)}") 
    
    def read_plugin_logs(self, n_lines=50):
        """讀取插件日誌"""
        try:
            with open('plugin.log', 'r') as f:
                return f.readlines()[-n_lines:]
        except FileNotFoundError:
            return ['No plugin logs found'] 