import pytest
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from voting.models import Election, Contest, ContestCandidate, ElectoralRoll, Vote


# ─────────────────────────────────────────
# ELECTION MODEL — sync_status()
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestElectionSyncStatus:

    def test_future_election_is_pending(self, pending_election):
        pending_election.sync_status()
        assert pending_election.status == 'pending'

    def test_ongoing_election_is_active(self, active_election):
        active_election.sync_status()
        assert active_election.status == 'active'

    def test_past_election_is_closed(self, closed_election):
        closed_election.sync_status()
        assert closed_election.status == 'closed'


# ─────────────────────────────────────────
# OWNERSHIP — organizers can't touch each other's elections
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestElectionOwnership:

    def test_non_owner_gets_404_on_detail(self, client, other_organizer, active_election):
        client.force_login(other_organizer)
        response = client.get(reverse('voting:election_detail', args=[active_election.pk]))
        assert response.status_code == 404

    def test_owner_can_view_detail(self, client, organizer, active_election):
        client.force_login(organizer)
        response = client.get(reverse('voting:election_detail', args=[active_election.pk]))
        assert response.status_code == 200

    def test_non_owner_cannot_delete(self, client, other_organizer, active_election):
        client.force_login(other_organizer)
        response = client.post(reverse('voting:delete_election', args=[active_election.pk]))
        assert response.status_code == 404
        assert Election.objects.filter(pk=active_election.pk).exists()


# ─────────────────────────────────────────
# EDIT ELECTION — only while pending
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestEditElectionGuard:

    def test_can_edit_pending_election(self, client, organizer, pending_election):
        client.force_login(organizer)
        response = client.post(
            reverse('voting:edit_election', args=[pending_election.pk]),
            {
                'title': 'Renamed',
                'description': '',
                'start_date': pending_election.start_date,
                'end_date': pending_election.end_date,
            }
        )
        assert response.status_code == 302
        pending_election.refresh_from_db()
        assert pending_election.title == 'Renamed'

    def test_cannot_edit_active_election(self, client, organizer, active_election):
        client.force_login(organizer)
        response = client.get(reverse('voting:edit_election', args=[active_election.pk]))
        assert response.status_code == 302
        assert response.url == reverse('voting:election_detail', args=[active_election.pk])


# ─────────────────────────────────────────
# ELECTORAL ROLL UPLOAD — dedup
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestElectoralRollUpload:

    def test_duplicate_emails_are_skipped(self, client, organizer, active_election):
        client.force_login(organizer)
        ElectoralRoll.objects.create(election=active_election, email='dupe@example.com')
        client.post(
            reverse('voting:upload_electoral_roll', args=[active_election.pk]),
            {'emails': 'dupe@example.com\nnew@example.com'}
        )
        assert ElectoralRoll.objects.filter(election=active_election).count() == 2


# ─────────────────────────────────────────
# PUBLIC BALLOT GUARDS (token-based, no login)
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestBallotGuards:

    def test_used_roll_shows_used_page(self, client, roll_entry):
        roll_entry.used = True
        roll_entry.save()
        response = client.get(reverse('voting:ballot', args=[roll_entry.token]))
        assert [t.name for t in response.templates if t.name] == ['voting/ballot_used.html']

    def test_pending_election_shows_pending_page(self, client, pending_election):
        roll = ElectoralRoll.objects.create(election=pending_election, email='p@example.com')
        response = client.get(reverse('voting:ballot', args=[roll.token]))
        assert 'voting/ballot_pending.html' in [t.name for t in response.templates if t.name]

    def test_closed_election_shows_closed_page(self, client, closed_election):
        roll = ElectoralRoll.objects.create(election=closed_election, email='c@example.com')
        response = client.get(reverse('voting:ballot', args=[roll.token]))
        assert 'voting/ballot_closed.html' in [t.name for t in response.templates if t.name]

    def test_active_election_shows_ballot(self, client, roll_entry, plurality_contest, candidates):
        response = client.get(reverse('voting:ballot', args=[roll_entry.token]))
        assert response.status_code == 200
        assert 'voting/ballot.html' in [t.name for t in response.templates if t.name]

    def test_invalid_token_returns_404(self, client):
        import uuid
        response = client.get(reverse('voting:ballot', args=[uuid.uuid4()]))
        assert response.status_code == 404


# ─────────────────────────────────────────
# SUBMIT VOTE — plurality
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitVotePlurality:

    def test_vote_recorded_and_roll_marked_used(self, client, roll_entry, plurality_contest, candidates):
        response = client.post(
            reverse('voting:submit_vote', args=[roll_entry.token]),
            {f'contest_{plurality_contest.pk}': [str(candidates[0].pk)]}
        )
        roll_entry.refresh_from_db()
        assert response.status_code == 302
        assert roll_entry.used is True
        assert Vote.objects.filter(electoral_roll=roll_entry).count() == 1

    def test_selecting_more_than_seats_rejected(self, client, roll_entry, plurality_contest, candidates):
        # plurality_contest has seats=1, so selecting both candidates should be rejected
        client.post(
            reverse('voting:submit_vote', args=[roll_entry.token]),
            {f'contest_{plurality_contest.pk}': [str(c.pk) for c in candidates]}
        )
        roll_entry.refresh_from_db()
        assert roll_entry.used is False
        assert Vote.objects.filter(electoral_roll=roll_entry).count() == 0

    def test_no_selection_rejected(self, client, roll_entry, plurality_contest, candidates):
        client.post(reverse('voting:submit_vote', args=[roll_entry.token]), {})
        roll_entry.refresh_from_db()
        assert roll_entry.used is False

    def test_cannot_vote_twice(self, client, roll_entry, plurality_contest, candidates):
        roll_entry.used = True
        roll_entry.save()
        client.post(
            reverse('voting:submit_vote', args=[roll_entry.token]),
            {f'contest_{plurality_contest.pk}': [str(candidates[0].pk)]}
        )
        assert Vote.objects.filter(electoral_roll=roll_entry).count() == 0


# ─────────────────────────────────────────
# SUBMIT VOTE — ranked choice
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitVoteRankedChoice:

    def test_ranked_vote_recorded(self, client, active_election):
        contest = Contest.objects.create(
            election=active_election, title='Board',
            voting_method='ranked_choice', seats=1
        )
        c1 = ContestCandidate.objects.create(contest=contest, name='X')
        c2 = ContestCandidate.objects.create(contest=contest, name='Y')
        roll = ElectoralRoll.objects.create(election=active_election, email='r@example.com')

        client.post(
            reverse('voting:submit_vote', args=[roll.token]),
            {
                f'rank_{contest.pk}_{c1.pk}': '1',
                f'rank_{contest.pk}_{c2.pk}': '2',
            }
        )
        roll.refresh_from_db()
        assert roll.used is True
        assert Vote.objects.filter(electoral_roll=roll).count() == 2
        assert Vote.objects.get(contest_candidate=c1).rank == 1

    def test_no_ranks_rejected(self, client, active_election):
        contest = Contest.objects.create(
            election=active_election, title='Board',
            voting_method='ranked_choice', seats=1
        )
        ContestCandidate.objects.create(contest=contest, name='X')
        roll = ElectoralRoll.objects.create(election=active_election, email='r2@example.com')

        client.post(reverse('voting:submit_vote', args=[roll.token]), {})
        roll.refresh_from_db()
        assert roll.used is False


# ─────────────────────────────────────────
# ELECTION RESULTS
# ─────────────────────────────────────────

@pytest.mark.django_db
class TestElectionResults:

    def test_plurality_results_counted_correctly(
        self, client, organizer, active_election, plurality_contest, candidates
    ):
        roll1 = ElectoralRoll.objects.create(election=active_election, email='a@example.com')
        roll2 = ElectoralRoll.objects.create(election=active_election, email='b@example.com')
        Vote.objects.create(electoral_roll=roll1, contest_candidate=candidates[0])
        Vote.objects.create(electoral_roll=roll2, contest_candidate=candidates[0])

        client.force_login(organizer)
        response = client.get(reverse('voting:election_results', args=[active_election.pk]))
        assert response.status_code == 200

        results = response.context['results']
        assert results[0]['total_votes'] == 2
        assert results[0]['candidate_results'][0]['votes'] == 2
        assert results[0]['candidate_results'][0]['percentage'] == 100.0

        