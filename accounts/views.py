from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
# Create your views here.
def login(request):
    if request.method == 'POST':
        user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            return render(request, 'accounts/login.html', {'error':'username or password is incorrect'})
    else:
        return render(request, 'accounts/login.html')

@login_required
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        request.session.flush()
        return redirect('login')
    return render(request, 'accounts/login.html')
