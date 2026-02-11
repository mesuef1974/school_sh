
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def root_view(request):
    return HttpResponse("Django is running, but no app URLs are included yet.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_view),
]