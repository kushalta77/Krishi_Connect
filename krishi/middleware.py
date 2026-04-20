"""
Request/Response Logging Middleware
Logs all incoming requests and outgoing responses with detailed information
"""

import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import QueryDict
import traceback

request_logger = logging.getLogger('django.request')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests and responses
    """
    
    def process_request(self, request):
        """Log incoming request"""
        try:
            # Build request log message
            log_data = {
                'method': request.method,
                'path': request.path,
                'client_ip': self.get_client_ip(request),
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'content_type': request.META.get('CONTENT_TYPE', 'N/A'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'N/A')[:100],  # Truncate for brevity
            }
            
            # Add query parameters if present
            if request.GET:
                log_data['query_params'] = dict(request.GET.lists())
            
            # Add POST data for certain content types
            if request.method == 'POST' and request.content_type:
                if 'application/json' in request.content_type:
                    try:
                        log_data['post_data'] = json.loads(request.body.decode('utf-8'))
                    except:
                        pass
                elif 'form' in request.content_type:
                    log_data['post_keys'] = list(request.POST.keys())
            
            request_logger.info(f"[REQUEST] {log_data}")
            
        except Exception as e:
            request_logger.error(f"Error logging request: {str(e)}")
        
        return None  # Continue processing
    
    def process_response(self, request, response):
        """Log outgoing response"""
        try:
            log_data = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'content_type': response.get('Content-Type', 'N/A'),
                'client_ip': self.get_client_ip(request),
            }
            
            request_logger.info(f"[RESPONSE] {log_data}")
            
        except Exception as e:
            request_logger.error(f"Error logging response: {str(e)}")
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions during request processing"""
        error_logger = logging.getLogger('django')
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'client_ip': self.get_client_ip(request),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'traceback': traceback.format_exc()
        }
        
        error_logger.error(f"[EXCEPTION] {log_data}")
        
        return None  # Return None to use default error handling
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
