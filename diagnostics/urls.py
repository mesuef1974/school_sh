from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('plan/', include([
        path('', views.plan_list_view, name='plan_list'),
    ])),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
]