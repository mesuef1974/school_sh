
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def root_view(request):
    return HttpResponse("Django is running, but no app URLs are included yet.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_view),
    # path('api/memory/', include('project_memory.urls')), # REMOVED as requested
]