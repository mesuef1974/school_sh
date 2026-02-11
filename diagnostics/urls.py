from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.plan_list, name='dashboard'),
    path('plan/', include([
        path('', views.plan_list, name='plan_list'),
    ])),
    path('auth/login/', views.CustomLoginView.as_view(), name='login'),
]