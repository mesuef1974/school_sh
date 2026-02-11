from django.urls import path
from django.http import HttpResponse


from .views import dashboard_views

urlpatterns = [
    path('', dashboard_views.dashboard_view, name='dashboard'),
]