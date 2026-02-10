from django.urls import path
from .views.plan_views import (
    plan_list, plan_edit_modal, plan_edit_save, 
    plan_evaluate_modal, plan_evaluate_save,
    plan_toggle_evidence_request,
    plan_upload_evidence_modal, plan_upload_evidence_save
)
from .views.auth_views import CustomLoginView
from .views.dashboard_views import dashboard_view # سيتم إنشاؤه لاحقاً
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # Dashboard
    path('', dashboard_view, name='dashboard'),

    # Auth URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Plan URLs
    path('plan/', plan_list, name='plan_list'),
    
    # Edit (Execution) URLs
    path('plan/<int:pk>/edit/', plan_edit_modal, name='plan_edit_modal'),
    path('plan/<int:pk>/edit/save/', plan_edit_save, name='plan_edit_save'),
    
    # Evaluate URLs
    path('plan/<int:pk>/evaluate/', plan_evaluate_modal, name='plan_evaluate_modal'),
    path('plan/<int:pk>/evaluate/save/', plan_evaluate_save, name='plan_evaluate_save'),
    path('plan/<int:pk>/evidence-request/toggle/', plan_toggle_evidence_request, name='plan_toggle_evidence_request'),
    path('plan/<int:pk>/upload-evidence/', plan_upload_evidence_modal, name='plan_upload_evidence_modal'),
    path('plan/<int:pk>/upload-evidence/save/', plan_upload_evidence_save, name='plan_upload_evidence_save'),
]