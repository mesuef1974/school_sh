
from django.urls import path
from django.http import HttpResponse

def temp_view(request):
    return HttpResponse("Diagnostics URLs are working!")

urlpatterns = [
    path('', temp_view, name='dashboard'),
]