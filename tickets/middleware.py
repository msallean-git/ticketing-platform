from django_ratelimit.exceptions import Ratelimited
from django.http import HttpResponse


class RatelimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return HttpResponse('Too Many Requests', status=429)
        return None
