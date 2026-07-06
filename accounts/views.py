from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from .models import CustomUser, PasswordResetOTP
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta



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


def forgot_password(request):
    """Step 1 — User enters email, system sends OTP."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
 
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'accounts/forgot_password.html')
 
        # Always show the same message whether email exists or not
        # (prevents email enumeration attacks)
        try:
            user = CustomUser.objects.get(email=email)
 
            # Invalidate any existing unused OTPs for this user
            PasswordResetOTP.objects.filter(
                user=user, is_used=False
            ).update(is_used=True)
 
            # Generate new OTP
            otp        = PasswordResetOTP.generate_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
 
            PasswordResetOTP.objects.create(
                user=user,
                otp=otp,
                expires_at=expires_at,
            )
 
            # Send OTP email
            send_mail(
                subject="iVote — Your Password Reset OTP",
                message=(
                    f"Hello {user.first_name},\n\n"
                    f"You requested a password reset for your iVote account.\n\n"
                    f"Your One-Time Password (OTP) is:\n\n"
                    f"    {otp}\n\n"
                    f"This OTP is valid for 10 minutes.\n"
                    f"Do not share this code with anyone.\n\n"
                    f"If you did not request this, please ignore this email.\n\n"
                    f"— iVote Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
 
        except CustomUser.DoesNotExist:
            messages.error(
                request,
                "Unable to send OTP. Please check the email address and try again."
            )
            return render(request, 'accounts/forgot_password.html')
            
 
        # Store email in session for next step
        request.session['reset_email'] = email
 
        messages.success(
            request,
            "OTP sent successfully. Please check your inbox (and spam folder)."
        )
        return redirect('verify_otp')
 
    return render(request, 'accounts/forgot_password.html')
 
 
def verify_otp(request):
    """Step 2 — User enters the 6-digit OTP."""
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired. Please start again.")
        return redirect('forgot_password')
 
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
 
        if not otp_entered or not otp_entered.isdigit() or len(otp_entered) != 6:
            messages.error(request, "Please enter a valid 6-digit OTP.")
            return render(request, 'accounts/verify_otp.html', {'email': email})
 
        try:
            user = CustomUser.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(
                user=user,
                otp=otp_entered,
                is_used=False,
            ).order_by('-created_at').first()
 
            if otp_obj and otp_obj.is_valid():
                # Mark OTP as used
                otp_obj.is_used = True
                otp_obj.save(update_fields=['is_used'])
 
                # Store verified flag in session
                request.session['reset_verified'] = True
                return redirect('reset_password')
            else:
                messages.error(
                    request,
                    "Invalid or expired OTP. Please try again or request a new one."
                )
        except CustomUser.DoesNotExist:
            messages.error(request, "Something went wrong. Please start again.")
            return redirect('forgot_password')
 
    return render(request, 'accounts/verify_otp.html', {'email': email})
 
 
def reset_password(request):
    """Step 3 — User sets a new password."""
    email    = request.session.get('reset_email')
    verified = request.session.get('reset_verified')
 
    if not email or not verified:
        messages.error(request, "Session expired. Please start again.")
        return redirect('forgot_password')
 
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
 
        if not password1 or not password2:
            messages.error(request, "Please fill in both password fields.")
            return render(request, 'accounts/reset_password.html')
 
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/reset_password.html')
 
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'accounts/reset_password.html')
 
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(password1)
            user.save(update_fields=['password'])
 
            # Clear session
            del request.session['reset_email']
            del request.session['reset_verified']
 
            messages.success(
                request,
                "Password reset successfully. You can now log in with your new password."
            )
            return redirect('login')
 
        except CustomUser.DoesNotExist:
            messages.error(request, "Something went wrong. Please start again.")
            return redirect('forgot_password')
 
    return render(request, 'accounts/reset_password.html')

