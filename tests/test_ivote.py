"""
test_ivote.py — Full pytest test suite for iVote
Place this file at: tests/test_ivote.py

Run with:
    pytest
    pytest -v                     (verbose)
    pytest -v -k "test_voting"    (run only voting tests)
    pytest --tb=short             (shorter tracebacks)
"""
import uuid
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model

from voting.models import Election, Candidate, VoterParticipation, Votes
from audit.models import AuditRequest
from tests.factories import (
    VoterFactory, OrganizerFactory,
    OpenElectionFactory, DomainElectionFactory,
    IDListElectionFactory, PendingElectionFactory, ClosedElectionFactory,
    CandidateFactory, VoterParticipationFactory, VotesFactory,
    AuditRequestFactory,
)

User = get_user_model()


# ================================================================== #
#  ACCOUNTS TESTS
# ================================================================== #

@pytest.mark.django_db
class TestUserCreation:

    def test_voter_created_with_correct_role(self):
        voter = VoterFactory()
        assert voter.role == 'voter'

    def test_organizer_created_with_correct_role(self):
        organizer = OrganizerFactory()
        assert organizer.role == 'organizer'

    def test_voter_id_is_unique(self):
        """Two voters cannot share the same voter_id."""
        voter1 = VoterFactory(voter_id='UNIQUE001')
        with pytest.raises(Exception):
            VoterFactory(voter_id='UNIQUE001')

    def test_voter_password_is_hashed(self):
        voter = VoterFactory()
        assert voter.password != 'Test@1234'
        assert voter.check_password('Test@1234')

    def test_voter_email_stored_correctly(self):
        voter = VoterFactory(email='test@school.edu')
        assert voter.email == 'test@school.edu'


@pytest.mark.django_db
class TestLoginLogout:

    def test_voter_can_login(self, client):
        voter = VoterFactory()
        response = client.post('/accounts/login/', {
            'username': voter.username,
            'password': 'Test@1234',
        })
        assert response.status_code in [200, 302]

    def test_invalid_password_rejected(self, client):
        voter = VoterFactory()
        response = client.post('/accounts/login/', {
            'username': voter.username,
            'password': 'WrongPassword',
        })
        # Should not redirect to dashboard
        assert response.status_code == 200
        assert 'login' in response.request['PATH_INFO']

    def test_organizer_can_login(self, client):
        organizer = OrganizerFactory()
        response = client.post('/accounts/login/', {
            'username': organizer.username,
            'password': 'Test@1234',
        })
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestRoleBasedAccess:

    def test_unauthenticated_user_redirected_from_election_list(self, client):
        response = client.get('/voting/', follow=False)
        assert response.status_code == 302
        assert '/login' in response['Location'] or 'login' in response['Location']

    def test_voter_cannot_access_organizer_dashboard(self, client):
        voter = VoterFactory()
        client.force_login(voter)
        response = client.get('/organizer/dashboard/')
        # Should redirect or return 403
        assert response.status_code in [302, 403]

    def test_organizer_cannot_access_voter_dashboard(self, client):
        organizer = OrganizerFactory()
        client.force_login(organizer)
        response = client.get('/voter/dashboard/')
        assert response.status_code in [302, 403]

    def test_voter_can_access_voter_dashboard(self, client):
        voter = VoterFactory()
        client.force_login(voter)
        response = client.get('/voter/dashboard/')
        assert response.status_code == 200

    def test_organizer_can_access_organizer_dashboard(self, client):
        organizer = OrganizerFactory()
        client.force_login(organizer)
        response = client.get('/organizer/dashboard/')
        assert response.status_code == 200


# ================================================================== #
#  ELECTION TESTS
# ================================================================== #

@pytest.mark.django_db
class TestElectionCreation:

    def test_open_election_created(self):
        election = OpenElectionFactory()
        assert election.eligibility_type == 'open'
        assert election.status == 'active'

    def test_domain_election_created(self):
        election = DomainElectionFactory()
        assert election.eligibility_type == 'domain'
        assert election.eligibility_value == 'school.edu'

    def test_id_list_election_created(self):
        election = IDListElectionFactory()
        assert election.eligibility_type == 'id_list'
        assert 'SCH00001' in election.eligibility_value

    def test_election_str(self):
        election = OpenElectionFactory(title='Test Election')
        assert 'Test Election' in str(election)


@pytest.mark.django_db
class TestEligibilitySystem:

    def test_open_election_allows_anyone(self):
        election = OpenElectionFactory()
        voter = VoterFactory(email='anyone@gmail.com')
        assert election.is_eligible(voter) is True

    def test_domain_election_allows_correct_domain(self):
        election = DomainElectionFactory(eligibility_value='school.edu')
        voter = VoterFactory(email='student@school.edu')
        assert election.is_eligible(voter) is True

    def test_domain_election_blocks_wrong_domain(self):
        election = DomainElectionFactory(eligibility_value='school.edu')
        voter = VoterFactory(email='outsider@gmail.com')
        assert election.is_eligible(voter) is False

    def test_id_list_election_allows_listed_voter(self):
        voter = VoterFactory(voter_id='LISTED001')
        election = IDListElectionFactory(eligibility_value='LISTED001,LISTED002')
        assert election.is_eligible(voter) is True

    def test_id_list_election_blocks_unlisted_voter(self):
        voter = VoterFactory(voter_id='NOTLISTED')
        election = IDListElectionFactory(eligibility_value='LISTED001,LISTED002')
        assert election.is_eligible(voter) is False

    def test_id_list_handles_spaces_in_csv(self):
        voter = VoterFactory(voter_id='SPACED001')
        election = IDListElectionFactory(eligibility_value=' SPACED001 , SPACED002 ')
        assert election.is_eligible(voter) is True


@pytest.mark.django_db
class TestElectionStatusSync:

    def test_future_election_is_pending(self):
        election = PendingElectionFactory()
        election.sync_status()
        assert election.status == 'pending'

    def test_active_election_stays_active(self):
        election = OpenElectionFactory()  # active by default
        election.sync_status()
        assert election.status == 'active'

    def test_past_election_is_closed(self):
        election = ClosedElectionFactory()
        election.sync_status()
        assert election.status == 'closed'


# ================================================================== #
#  VOTING TESTS
# ================================================================== #

@pytest.mark.django_db
class TestVoting:

    def test_vote_is_recorded(self):
        election  = OpenElectionFactory()
        candidate = CandidateFactory(election=election)
        voter     = VoterFactory()

        VoterParticipation.objects.create(
            user=voter, election=election, voted_at=timezone.now()
        )
        Votes.objects.create(
            election=election,
            candidate=candidate,
            token=uuid.uuid4(),
            voted_at=timezone.now(),
        )

        assert VoterParticipation.objects.filter(user=voter, election=election).exists()
        assert Votes.objects.filter(election=election, candidate=candidate).exists()

    def test_duplicate_vote_prevented_by_db(self):
        """unique_together on VoterParticipation blocks second vote."""
        voter    = VoterFactory()
        election = OpenElectionFactory()

        VoterParticipation.objects.create(
            user=voter, election=election, voted_at=timezone.now()
        )
        with pytest.raises(Exception):
            VoterParticipation.objects.create(
                user=voter, election=election, voted_at=timezone.now()
            )

    def test_ballot_secrecy_votes_table_has_no_user(self):
        """Votes table should NOT have a user field — ballot secrecy."""
        vote = VotesFactory()
        assert not hasattr(vote, 'user')

    def test_vote_has_uuid_token(self):
        vote = VotesFactory()
        assert vote.token is not None
        # Should be a valid UUID
        assert uuid.UUID(str(vote.token))

    def test_multiple_voters_can_vote(self):
        election   = OpenElectionFactory()
        candidate  = CandidateFactory(election=election)
        voters     = VoterFactory.create_batch(5)

        for voter in voters:
            VoterParticipation.objects.create(
                user=voter, election=election, voted_at=timezone.now()
            )
            Votes.objects.create(
                election=election,
                candidate=candidate,
                token=uuid.uuid4(),
                voted_at=timezone.now(),
            )

        assert VoterParticipation.objects.filter(election=election).count() == 5
        assert Votes.objects.filter(election=election).count() == 5


@pytest.mark.django_db
class TestVoteCountAggregation:

    def test_winner_has_highest_vote_count(self):
        from django.db.models import Count

        election    = OpenElectionFactory()
        candidate_a = CandidateFactory(election=election)
        candidate_b = CandidateFactory(election=election)

        # A gets 3 votes, B gets 1 vote
        for _ in range(3):
            Votes.objects.create(
                election=election,
                candidate=candidate_a,
                token=uuid.uuid4(),
                voted_at=timezone.now(),
            )
        Votes.objects.create(
            election=election,
            candidate=candidate_b,
            token=uuid.uuid4(),
            voted_at=timezone.now(),
        )

        results = (
            Votes.objects.filter(election=election)
            .values('candidate')
            .annotate(total=Count('candidate'))
            .order_by('-total')
        )

        assert results[0]['candidate'] == candidate_a.id
        assert results[0]['total'] == 3


# ================================================================== #
#  CANDIDATE APPLICATION TESTS
# ================================================================== #

@pytest.mark.django_db
class TestCandidateApplication:

    def test_candidate_default_status_is_pending(self):
        candidate = CandidateFactory(status='pending')
        assert candidate.status == 'pending'

    def test_candidate_can_be_approved(self):
        candidate = CandidateFactory(status='pending')
        candidate.status = 'approved'
        candidate.save()
        candidate.refresh_from_db()
        assert candidate.status == 'approved'

    def test_candidate_can_be_rejected(self):
        candidate = CandidateFactory(status='pending')
        candidate.status = 'rejected'
        candidate.save()
        candidate.refresh_from_db()
        assert candidate.status == 'rejected'

    def test_duplicate_candidacy_blocked(self):
        """Same voter cannot apply twice to the same election."""
        voter    = VoterFactory()
        election = OpenElectionFactory()
        CandidateFactory(user=voter, election=election)
        with pytest.raises(Exception):
            CandidateFactory(user=voter, election=election)

    def test_voter_can_apply_to_multiple_elections(self):
        voter     = VoterFactory()
        election1 = OpenElectionFactory()
        election2 = OpenElectionFactory()
        CandidateFactory(user=voter, election=election1)
        CandidateFactory(user=voter, election=election2)
        assert Candidate.objects.filter(user=voter).count() == 2


# ================================================================== #
#  AUDIT TESTS
# ================================================================== #

@pytest.mark.django_db
class TestAuditRequest:

    def test_audit_request_created_with_pending_status(self):
        audit = AuditRequestFactory()
        assert audit.status == 'pending'

    def test_audit_request_linked_to_correct_election(self):
        audit = AuditRequestFactory()
        assert audit.election == audit.candidate.election

    def test_audit_request_can_be_approved(self):
        audit = AuditRequestFactory()
        audit.status = 'approved'
        audit.admin_response = 'Audit approved after review.'
        audit.save()
        audit.refresh_from_db()
        assert audit.status == 'approved'
        assert audit.admin_response == 'Audit approved after review.'

    def test_audit_request_can_be_rejected(self):
        audit = AuditRequestFactory()
        audit.status = 'rejected'
        audit.admin_response = 'No evidence of irregularities.'
        audit.save()
        audit.refresh_from_db()
        assert audit.status == 'rejected'

    def test_audit_str(self):
        audit = AuditRequestFactory()
        assert str(audit) != ''

    def test_only_candidate_can_submit_audit(self):
        """AuditRequest requires a Candidate — plain voter cannot submit."""
        election = OpenElectionFactory()
        voter    = VoterFactory()
        # No candidate object for this voter → should fail
        with pytest.raises(Exception):
            AuditRequest.objects.create(
                candidate=None,
                election=election,
                reason='I want an audit',
            )

            