
from django.shortcuts import render
from django.contrib.auth.models import User

def users_list(request):
    q = request.GET.get('q','')
    users = User.objects.all()
    if q:
        users = users.filter(username__icontains=q)
    return render(request, 'users/list.html', {'users': users, 'q': q})
