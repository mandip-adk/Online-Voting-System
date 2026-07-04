import pytest
from django.urls import reverse

from accounts.models import CustomUser


# ─────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestCustomUserModel:

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError):
            CustomUser.objects.create_user(email='', password='pass12345')

    def test_create_user_normalizes_email_domain(self):
        user = CustomUser.objects.create_user(
            email='Test@EXAMPLE.COM', password='pass12345',
            first_name='T', last_name='U'
        )
        # normalize_email lowercases only the domain part, not the local part
        assert user.email == 'Test@example.com'

    def test_default_role_is_organizer(self):
        user = CustomUser.objects.create_user(
            email='defaultrole@example.com', password='pass12345',
            first_name='D', last_name='R'
        )
        assert user.role == 'organizer'

    def test_create_superuser_sets_admin_role_and_flags(self):
        admin = CustomUser.objects.create_superuser(
            email='root@example.com', password='pass12345',
            first_name='R', last_name='T'
        )
        assert admin.role == 'admin'
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_get_full_name(self):
        user = CustomUser(first_name='Jane', last_name='Doe')
        assert user.get_full_name() == 'Jane Doe'


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterView:

    def test_register_creates_organizer(self, client):
        response = client.post(reverse('register'), {
            'first_name': 'New',
            'last_name': 'Org',
            'email': 'neworg@example.com',
            'role': 'organizer',
            'organization_name': 'ACME',
            'country': 'Nepal',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        assert response.status_code == 302
        assert CustomUser.objects.filter(email='neworg@example.com').exists()

    def test_register_password_mismatch_does_not_create_user(self, client):
        response = client.post(reverse('register'), {
            'first_name': 'New',
            'last_name': 'Org',
            'email': 'mismatch@example.com',
            'role': 'organizer',
            'password1': 'StrongPass123',
            'password2': 'DifferentPass123',
        })
        assert response.status_code == 200  # re-rendered form with errors
        assert not CustomUser.objects.filter(email='mismatch@example.com').exists()

    def test_register_duplicate_email_rejected(self, client, organizer):
        response = client.post(reverse('register'), {
            'first_name': 'Dup',
            'last_name': 'Licate',
            'email': organizer.email,
            'role': 'organizer',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })
        assert response.status_code == 200
        assert CustomUser.objects.filter(email=organizer.email).count() == 1


# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestLoginView:

    def test_login_with_correct_credentials_redirects_organizer(self, client, organizer):
        response = client.post(reverse('login'), {
            'username': organizer.email,
            'password': 'testpass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('organizer_dashboard')

    def test_login_with_wrong_password_rerenders_form(self, client, organizer):
        response = client.post(reverse('login'), {
            'username': organizer.email,
            'password': 'wrongpassword',
        })
        assert response.status_code == 200

    def test_admin_login_redirects_to_admin_dashboard(self, client, admin_user):
        response = client.post(reverse('login'), {
            'username': admin_user.email,
            'password': 'testpass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('admin_dashboard')


# ─────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutView:

    def test_logout_redirects_to_login(self, client, organizer):
        client.force_login(organizer)
        response = client.get(reverse('logout'))
        assert response.status_code == 302
        assert response.url == reverse('login')


# ─────────────────────────────────────────
# DASHBOARD ACCESS / ROLE GATING
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestDashboardAccess:

    def test_organizer_dashboard_requires_login(self, client):
        response = client.get(reverse('organizer_dashboard'))
        assert response.status_code == 302  # redirected to login

    def test_organizer_can_access_organizer_dashboard(self, client, organizer):
        client.force_login(organizer)
        response = client.get(reverse('organizer_dashboard'))
        assert response.status_code == 200

    def test_organizer_is_bounced_from_admin_dashboard(self, client, organizer):
        client.force_login(organizer)
        response = client.get(reverse('admin_dashboard'))
        assert response.status_code == 302
        assert response.url == reverse('home')

    def test_admin_can_access_admin_dashboard(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('admin_dashboard'))
        assert response.status_code == 200
        assert 'total_organizers' in response.context
        assert 'total_admins' in response.context

        