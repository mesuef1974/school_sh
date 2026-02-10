
from django.shortcuts import render
from django.contrib.auth.models import Group, Permission

def roles_list(request):
    roles = Group.objects.all().prefetch_related('permissions')
    perms = Permission.objects.all()
    return render(request, 'authz/list.html', {'roles': roles, 'perms': perms})
