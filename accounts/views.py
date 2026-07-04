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
        email    = request.POST.get('username')  # our login form sends field as 'username'
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
        return redirect('organizer_dashboard')
    return render(request, 'home.html')


@login_required
def organizer_dashboard(request):
    if request.user.role not in ('organizer', 'admin') and not request.user.is_superuser:
        return redirect('home')

    from voting.models import Election

    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')
    for e in elections:
        e.sync_status()
    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')

    items = []
    total_vote_cast = 0
    for e in elections:
        roll = e.electoral_roll.all()
        voted = roll.filter(used=True).count()
        total = roll.count()
        items.append({'election': e, 'voted': voted, 'total': total})
        total_vote_cast += voted

    return render(request, 'voting/dashboard/organizer_dashboard.html', {
        'election_with_vote_count': items,
        'total_elections': elections.count(),
        'active_count':    elections.filter(status='active').count(),
        'pending_count':   elections.filter(status='pending').count(),
        'closed_count':    elections.filter(status='closed').count(),
        'total_vote_cast': total_vote_cast,
    })


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')

    total_organizers = CustomUser.objects.filter(role='organizer').count()
    total_admins     = CustomUser.objects.filter(role='admin').count()
    recent_users     = CustomUser.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')[:10]

    return render(request, 'voting/dashboard/admin_dashboard.html', {
        'total_organizers': total_organizers,
        'total_admins':     total_admins,
        'recent_users':     recent_users,
    })


def contact_us(request):
    from .forms import ContactForm
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # TODO: send email or save to DB later
            messages.success(request, "Your message has been sent successfully! We will get back to you soon.")
            return redirect('contact')
        else:
            messages.error(request, "Failed to send message. Please correct the errors in the form.")
    else:
        form = ContactForm()
    return render(request, 'contact_us.html', {'form': form})


def faqs(request):
    return render(request, 'faqs.html')


@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')


@login_required
def edit_profile(request):
    return render(request, 'accounts/edit_profile.html', {
        'user': request.user
    })


def about_view(request):
    return render(request, 'about.html')


def privacy_policy_view(request):
    return render(request, 'privacy_policy.html')


def terms_of_service_view(request):
    return render(request, 'terms_of_service.html')
