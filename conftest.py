import pytest
from datetime import timedelta

from django.utils import timezone

from accounts.models import CustomUser
from voting.models import Election, Contest, ContestCandidate, ElectoralRoll


# ─────────────────────────────────────────
# USERS
# ─────────────────────────────────────────

@pytest.fixture
def organizer(db):
    return CustomUser.objects.create_user(
        email='organizer@example.com',
        password='testpass123',
        first_name='Org',
        last_name='Anizer',
        role='organizer',
    )


@pytest.fixture
def other_organizer(db):
    """A second organizer, used to test that owners can't touch each other's data."""
    return CustomUser.objects.create_user(
        email='other@example.com',
        password='testpass123',
        first_name='Other',
        last_name='Organizer',
        role='organizer',
    )


@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_user(
        email='admin@example.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_staff=True,
    )


# ─────────────────────────────────────────
# ELECTIONS
# ─────────────────────────────────────────

@pytest.fixture
def active_election(organizer):
    now = timezone.now()
    return Election.objects.create(
        title='Active Election',
        created_by=organizer,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=1),
    )


@pytest.fixture
def pending_election(organizer):
    now = timezone.now()
    return Election.objects.create(
        title='Pending Election',
        created_by=organizer,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
    )


@pytest.fixture
def closed_election(organizer):
    now = timezone.now()
    return Election.objects.create(
        title='Closed Election',
        created_by=organizer,
        start_date=now - timedelta(days=5),
        end_date=now - timedelta(days=1),
    )


# ─────────────────────────────────────────
# CONTESTS / CANDIDATES / ROLL
# ─────────────────────────────────────────

@pytest.fixture
def plurality_contest(active_election):
    return Contest.objects.create(
        election=active_election,
        title='President',
        voting_method='plurality',
        seats=1,
    )


@pytest.fixture
def candidates(plurality_contest):
    c1 = ContestCandidate.objects.create(contest=plurality_contest, name='Alice')
    c2 = ContestCandidate.objects.create(contest=plurality_contest, name='Bob')
    return [c1, c2]


@pytest.fixture
def roll_entry(active_election):
    return ElectoralRoll.objects.create(election=active_election, email='voter@example.com')

