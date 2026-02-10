from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    """
    A custom login view that uses our themed template.
    """
    template_name = 'auth/login.html'
    # If the user is already logged in, redirect them to the home page.
    redirect_authenticated_user = True

    def get_success_url(self):
        # After a successful login, redirect to the main operational plan list.
        return reverse_lazy('plan_list')