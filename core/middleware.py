import logging
from datetime import datetime

logger = logging.getLogger('user.activity')

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 記錄請求
        if not request.path.startswith(('/static/', '/media/')):
            user = request.user.username if request.user.is_authenticated else 'Anonymous'
            timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
            with open('activity.log', 'a') as f:
                f.write(f'[{timestamp}] INFO: Request from {user} ({request.META.get("REMOTE_ADDR")}): {request.method} {request.path}\n')

        response = self.get_response(request)

        # 記錄響應
        if not request.path.startswith(('/static/', '/media/')):
            timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
            with open('activity.log', 'a') as f:
                f.write(f'[{timestamp}] INFO: Response to {user}: {response.status_code}\n')

        return response 