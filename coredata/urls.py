from django.urls import path, include
from coredata.views import dashboard_views, plan_views, auth_views # Import from coredata

urlpatterns = [
    path('', dashboard_views.dashboard_view, name='dashboard'),
    path('plan/', include([
        path('', plan_views.plan_list, name='plan_list'),
    ])),
    path('auth/login/', auth_views.CustomLoginView.as_view(), name='login'),
]