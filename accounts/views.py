from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from .models import CustomUser


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('organizer_dashboard')
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('organizer_dashboard')
    return redirect('login')


@login_required
def organizer_dashboard(request):
    if request.user.role not in ('organizer',) and not request.user.is_superuser:
        return redirect('home')
    return render(request, 'accounts/organizer_dashboard.html')


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')

    total_organizers = CustomUser.objects.filter(role='organizer').count()
    total_admins     = CustomUser.objects.filter(role='admin').count()
    recent_users     = CustomUser.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')[:10]

    return render(request, 'accounts/admin_dashboard.html', {
        'total_organizers': total_organizers,
        'total_admins':     total_admins,
        'recent_users':     recent_users,
    })

