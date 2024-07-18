from django.shortcuts import redirect
from django.urls import reverse

class RestrictUserDashboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/users/') and not request.user.is_authenticated:
            return redirect(reverse('login'))  # Redirect to login page if user is not authenticated

        response = self.get_response(request)
        return response