from django.urls import path
from django.http import HttpResponse


def temp_view(request):
    # هذه رسالة جديدة للتأكد من أن التغيير قد تم
    return HttpResponse("The file was saved correctly! Vercel is now connected.")


urlpatterns = [
    path('', temp_view, name='dashboard'),
]