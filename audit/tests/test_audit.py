import pytest
from django.urls import reverse

from audit.models import AuditRequest


# ─────────────────────────────────────────
# SUBMIT AUDIT REQUEST
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitAuditRequest:

    def test_owner_can_submit(self, client, organizer, active_election):
        client.force_login(organizer)
        response = client.post(
            reverse('audit:audit_request', args=[active_election.pk]),
            {'reason': 'Suspicious turnout numbers.'}
        )
        assert response.status_code == 302
        assert AuditRequest.objects.filter(election=active_election).exists()

    def test_non_owner_gets_404(self, client, other_organizer, active_election):
        client.force_login(other_organizer)
        response = client.post(
            reverse('audit:audit_request', args=[active_election.pk]),
            {'reason': 'Trying to audit someone else\'s election.'}
        )
        assert response.status_code == 404
        assert not AuditRequest.objects.filter(election=active_election).exists()

    def test_requires_login(self, client, active_election):
        response = client.get(reverse('audit:audit_request', args=[active_election.pk]))
        assert response.status_code == 302

    def test_empty_reason_rejected(self, client, organizer, active_election):
        client.force_login(organizer)
        response = client.post(
            reverse('audit:audit_request', args=[active_election.pk]),
            {'reason': ''}
        )
        assert response.status_code == 200  # re-rendered with form errors
        assert not AuditRequest.objects.filter(election=active_election).exists()


# ─────────────────────────────────────────
# AUDIT REQUEST LIST — admin only
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestAuditRequestList:

    def test_organizer_is_redirected_away(self, client, organizer):
        client.force_login(organizer)
        response = client.get(reverse('audit:audit_list'))
        # user_passes_test fails -> redirects (not a 403) since no exception is raised
        assert response.status_code == 302

    def test_admin_can_view(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse('audit:audit_list'))
        assert response.status_code == 200

    def test_status_counts_are_correct(self, client, admin_user, active_election):
        AuditRequest.objects.create(election=active_election, reason='One', status='pending')
        AuditRequest.objects.create(election=active_election, reason='Two', status='approved')
        AuditRequest.objects.create(election=active_election, reason='Three', status='rejected')

        client.force_login(admin_user)
        response = client.get(reverse('audit:audit_list'))
        assert response.context['pending_count'] == 1
        assert response.context['approved_count'] == 1
        assert response.context['rejected_count'] == 1


# ─────────────────────────────────────────
# AUDIT REVIEW — admin only
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestAuditReview:

    def test_admin_can_approve_with_response(self, client, admin_user, active_election):
        audit_request = AuditRequest.objects.create(election=active_election, reason='Check please')
        client.force_login(admin_user)
        response = client.post(
            reverse('audit:audit_review', args=[audit_request.pk]),
            {'status': 'approved', 'admin_response': 'Reviewed and approved.'}
        )
        audit_request.refresh_from_db()
        assert response.status_code == 302
        assert audit_request.status == 'approved'
        assert audit_request.admin_response == 'Reviewed and approved.'

    def test_approving_without_response_is_rejected_by_form(self, client, admin_user, active_election):
        audit_request = AuditRequest.objects.create(election=active_election, reason='Check please')
        client.force_login(admin_user)
        client.post(
            reverse('audit:audit_review', args=[audit_request.pk]),
            {'status': 'approved', 'admin_response': ''}
        )
        audit_request.refresh_from_db()
        assert audit_request.status == 'pending'  # unchanged — form validation blocked the save

    def test_organizer_cannot_review(self, client, organizer, active_election):
        audit_request = AuditRequest.objects.create(election=active_election, reason='Check please')
        client.force_login(organizer)
        response = client.get(reverse('audit:audit_review', args=[audit_request.pk]))
        assert response.status_code == 302


# ─────────────────────────────────────────
# AUDIT REPORT — any logged-in user
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestAuditReport:

    def test_any_logged_in_user_can_view(self, client, organizer, active_election):
        audit_request = AuditRequest.objects.create(election=active_election, reason='Check please')
        client.force_login(organizer)
        response = client.get(reverse('audit:audit_report', args=[audit_request.pk]))
        assert response.status_code == 200

    def test_requires_login(self, client, active_election):
        audit_request = AuditRequest.objects.create(election=active_election, reason='Check please')
        response = client.get(reverse('audit:audit_report', args=[audit_request.pk]))
        assert response.status_code == 302

        