
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from .models.plan import OperationalPlanItem

# Example helper to seed basic permissions/roles later via management command

def ensure_roles():
    content_type = ContentType.objects.get_for_model(OperationalPlanItem)
    perms = [
        ('plan_view', 'Can view operational plan'),
        ('plan_edit', 'Can edit operational plan'),
        ('plan_review', 'Can review operational plan'),
    ]
    created = []
    for codename, name in perms:
        p, _ = Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)
        created.append(p)
    # Example roles
    reviewers, _ = Group.objects.get_or_create(name='PlanReviewer')
    editors, _ = Group.objects.get_or_create(name='PlanEditor')
    viewers, _ = Group.objects.get_or_create(name='PlanViewer')
    reviewers.permissions.set([Permission.objects.get(codename='plan_view'), Permission.objects.get(codename='plan_review')])
    editors.permissions.set([Permission.objects.get(codename='plan_view'), Permission.objects.get(codename='plan_edit')])
    viewers.permissions.set([Permission.objects.get(codename='plan_view')])
    return created
