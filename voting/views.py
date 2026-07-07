from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from .models import Election, Contest, ContestCandidate, ElectoralRoll, Vote
from .forms import (
    ElectionForm, ContestForm, ContestCandidateForm,
    CSVUploadForm, EmailListForm
)


# ─────────────────────────────────────────
# ELECTION LIST
# ─────────────────────────────────────────

@login_required
def election_list(request):
    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')
    for e in elections:
        e.sync_status()
    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')

    # annotate each election with roll counts for template
    for e in elections:
        roll = e.electoral_roll.all()
        e.voted_count = roll.filter(used=True).count()
        e.total_count = roll.count()

    return render(request, 'voting/election_list.html', {
        'elections':     elections,
        'active_count':  elections.filter(status='active').count(),
        'pending_count': elections.filter(status='pending').count(),
        'closed_count':  elections.filter(status='closed').count(),
    })


# ─────────────────────────────────────────
# ELECTION DETAIL
# ─────────────────────────────────────────

@login_required
def election_detail(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    election.sync_status()
    contests = election.contests.prefetch_related('candidates').all()
    roll     = election.electoral_roll.all()
    voted    = roll.filter(used=True).count()
    total    = roll.count()

    return render(request, 'voting/election_detail.html', {
        'election': election,
        'contests': contests,
        'roll':     roll,
        'voted':    voted,
        'total':    total,
        'turnout':  round((voted / total * 100), 1) if total > 0 else 0,
    })


# ─────────────────────────────────────────
# CREATE ELECTION
# ─────────────────────────────────────────

@login_required
def create_election(request):
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save(commit=False)
            election.created_by = request.user
            election.save()
            messages.success(request, f"Election '{election.title}' created successfully.")
            return redirect('voting:election_detail', pk=election.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ElectionForm()
    return render(request, 'voting/create_election.html', {'form': form})


# ─────────────────────────────────────────
# EDIT ELECTION
# ─────────────────────────────────────────

@login_required
def edit_election(request, pk):
    election = get_object_or_404(
        Election,
        pk=pk,
        created_by=request.user
    )

    # Prevent editing once voting has started
    if election.start_date <= timezone.now():
        messages.error(
            request,
            "You can only edit elections that haven't started yet."
        )
        return redirect('voting:election_detail', pk=pk)

    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)

        if form.is_valid():
            form.save()
            messages.success(request, "Election updated successfully.")
            return redirect('voting:election_detail', pk=pk)

        messages.error(request, "Please correct the errors below.")

    else:
        form = ElectionForm(instance=election)

    return render(
        request,
        'voting/edit_election.html',
        {
            'form': form,
            'election': election,
        }
    )


# ─────────────────────────────────────────
# DELETE ELECTION
# ─────────────────────────────────────────

@login_required
def delete_election(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    if request.method == 'POST':
        title = election.title
        election.delete()
        messages.success(request, f"Election '{title}' deleted.")
        return redirect('voting:election_list')
    return render(request, 'voting/delete_election.html', {'election': election})


# ─────────────────────────────────────────
# ADD CONTEST
# ─────────────────────────────────────────

@login_required
def add_contest(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.election = election
            contest.save()
            messages.success(request, f"Contest '{contest.title}' added.")
            return redirect('voting:election_detail', pk=pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # auto-set order to next available
        next_order = election.contests.count()
        form = ContestForm(initial={'order': next_order})
    return render(request, 'voting/add_contest.html', {'form': form, 'election': election})


# ─────────────────────────────────────────
# EDIT CONTEST
# ─────────────────────────────────────────

@login_required
def edit_contest(request, pk, ck):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest  = get_object_or_404(Contest, pk=ck, election=election)
    if request.method == 'POST':
        form = ContestForm(request.POST, instance=contest)
        if form.is_valid():
            form.save()
            messages.success(request, "Contest updated.")
            return redirect('voting:election_detail', pk=pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContestForm(instance=contest)
    return render(request, 'voting/edit_contest.html', {
        'form': form, 'election': election, 'contest': contest
    })


# ─────────────────────────────────────────
# DELETE CONTEST
# ─────────────────────────────────────────

@login_required
def delete_contest(request, pk, ck):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest  = get_object_or_404(Contest, pk=ck, election=election)
    if request.method == 'POST':
        contest.delete()
        messages.success(request, "Contest deleted.")
        return redirect('voting:election_detail', pk=pk)
    return render(request, 'voting/delete_contest.html', {
        'election': election, 'contest': contest
    })


# ─────────────────────────────────────────
# ADD CANDIDATE TO CONTEST
# ─────────────────────────────────────────

@login_required
def add_candidate(request, pk, ck):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest  = get_object_or_404(Contest, pk=ck, election=election)
    if request.method == 'POST':
        form = ContestCandidateForm(request.POST)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.contest = contest
            candidate.save()
            messages.success(request, f"Candidate '{candidate.name}' added.")
            return redirect('voting:election_detail', pk=pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        next_order = contest.candidates.count()
        form = ContestCandidateForm(initial={'order': next_order})
    return render(request, 'voting/add_candidate.html', {
        'form': form, 'election': election, 'contest': contest
    })


# ─────────────────────────────────────────
# EDIT CANDIDATE
# ─────────────────────────────────────────

@login_required
def edit_candidate(request, pk, ck, cand_pk):
    election  = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest   = get_object_or_404(Contest, pk=ck, election=election)
    candidate = get_object_or_404(ContestCandidate, pk=cand_pk, contest=contest)
    if request.method == 'POST':
        form = ContestCandidateForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidate updated.")
            return redirect('voting:election_detail', pk=pk)
    else:
        form = ContestCandidateForm(instance=candidate)
    return render(request, 'voting/edit_candidate.html', {
        'form': form, 'election': election, 'contest': contest, 'candidate': candidate
    })


# ─────────────────────────────────────────
# DELETE CANDIDATE
# ─────────────────────────────────────────

@login_required
def delete_candidate(request, pk, ck, cand_pk):
    election  = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest   = get_object_or_404(Contest, pk=ck, election=election)
    candidate = get_object_or_404(ContestCandidate, pk=cand_pk, contest=contest)
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, "Candidate removed.")
        return redirect('voting:election_detail', pk=pk)
    return render(request, 'voting/delete_candidate.html', {
        'election': election, 'contest': contest, 'candidate': candidate
    })


# ─────────────────────────────────────────
# UPLOAD ELECTORAL ROLL
# ─────────────────────────────────────────

@login_required
def upload_electoral_roll(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)

    if request.method == 'POST':
        # Check which form was submitted
        if 'csv_file' in request.FILES:
            form     = CSVUploadForm(request.POST, request.FILES)
            form2    = EmailListForm()
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                emails   = _parse_csv_emails(csv_file)
                added, skipped = _add_to_roll(election, emails)
                messages.success(
                    request,
                    f"{added} voter(s) added to electoral roll. {skipped} duplicate(s) skipped."
                )
                return redirect('voting:election_detail', pk=pk)
        else:
            form  = CSVUploadForm()
            form2 = EmailListForm(request.POST)
            if form2.is_valid():
                emails = form2.cleaned_data['emails']
                added, skipped = _add_to_roll(election, emails)
                messages.success(
                    request,
                    f"{added} voter(s) added to electoral roll. {skipped} duplicate(s) skipped."
                )
                return redirect('voting:election_detail', pk=pk)
            else:
                messages.error(request, "Please correct the errors below.")
    else:
        form  = CSVUploadForm()
        form2 = EmailListForm()

    roll = election.electoral_roll.all().order_by('email')
    return render(request, 'voting/upload_electoral_roll.html', {
        'election': election,
        'form':     form,
        'form2':    form2,
        'roll':     roll,
    })


def _parse_csv_emails(csv_file):
    """Parse uploaded CSV/TXT file and return list of clean emails."""
    import csv, io
    emails = []
    decoded = csv_file.read().decode('utf-8', errors='ignore')
    reader  = csv.reader(io.StringIO(decoded))
    for row in reader:
        for cell in row:
            email = cell.strip().lower()
            if '@' in email and '.' in email:
                emails.append(email)
    return emails


def _add_to_roll(election, emails):
    """
    Bulk-add emails to electoral roll.

    Returns:
        (added, skipped)
    """
    added = 0
    skipped = 0

    for email in emails:
        email = email.strip().lower()

        if not email:
            continue

        if ElectoralRoll.objects.filter(
            election=election,
            email=email
        ).exists():
            skipped += 1
            continue

        ElectoralRoll.objects.create(
            election=election,
            email=email
        )
        added += 1

    return added, skipped


# ─────────────────────────────────────────
# VOTER PARTICIPATION
# ─────────────────────────────────────────

@login_required
def voter_participation(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    roll     = election.electoral_roll.all().order_by('email')
    voted    = roll.filter(used=True).count()
    total    = roll.count()
    return render(request, 'voting/voter_participation.html', {
        'election':  election,
        'roll':      roll,
        'voted':     voted,
        'total':     total,
        'not_voted': total - voted,
        'turnout':   round((voted / total * 100), 1) if total > 0 else 0,
    })


# ─────────────────────────────────────────
# ELECTION RESULTS
# ─────────────────────────────────────────

@login_required
def election_results(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    election.sync_status()
    contests = election.contests.prefetch_related('candidates').all()

    results = []
    for contest in contests:
        candidate_results = []
        total_votes = 0

        if contest.voting_method == 'plurality':
            for candidate in contest.candidates.all():
                vote_count = Vote.objects.filter(
                    contest_candidate=candidate
                ).count()
                total_votes += vote_count
                candidate_results.append({
                    'candidate':  candidate,
                    'votes':      vote_count,
                    'percentage': 0,
                })
            # calculate percentages
            for cr in candidate_results:
                cr['percentage'] = round(
                    (cr['votes'] / total_votes * 100) if total_votes > 0 else 0, 1
                )
            candidate_results.sort(key=lambda x: x['votes'], reverse=True)

        elif contest.voting_method == 'ranked_choice':
            # First preference counts for display
            for candidate in contest.candidates.all():
                vote_count = Vote.objects.filter(
                    contest_candidate=candidate, rank=1
                ).count()
                total_votes += vote_count
                candidate_results.append({
                    'candidate':  candidate,
                    'votes':      vote_count,
                    'percentage': 0,
                })
            for cr in candidate_results:
                cr['percentage'] = round(
                    (cr['votes'] / total_votes * 100) if total_votes > 0 else 0, 1
                )
            candidate_results.sort(key=lambda x: x['votes'], reverse=True)

        results.append({
            'contest':          contest,
            'candidate_results': candidate_results,
            'total_votes':      total_votes,
        })

    roll   = election.electoral_roll.all()
    voted  = roll.filter(used=True).count()
    total  = roll.count()

    return render(request, 'voting/election_results.html', {
        'election': election,
        'results':  results,
        'voted':    voted,
        'total':    total,
        'turnout':  round((voted / total * 100), 1) if total > 0 else 0,
    })


# ─────────────────────────────────────────
# SEND VOTING EMAILS
# ─────────────────────────────────────────

@login_required
def send_voting_emails(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)

    if request.method == 'POST':
        roll = election.electoral_roll.all()
        if not roll.exists():
            messages.error(request, "No voters in the electoral roll. Upload emails first.")
            return redirect('voting:election_detail', pk=pk)

        sent = 0
        failed = 0
        for entry in roll:
            ballot_url = request.build_absolute_uri(
                f'/voting/vote/{entry.token}/'
            )
            try:
                send_mail(
                    subject=f"You are invited to vote — {election.title}",
                    message=(
                        f"Dear Voter,\n\n"
                        f"You have been invited to participate in the following election:\n\n"
                        f"  {election.title}\n\n"
                        f"Click the link below to cast your vote:\n"
                        f"  {ballot_url}\n\n"
                        f"This link is unique to you. Do not share it.\n"
                        f"It will expire when the election closes on "
                        f"{election.end_date.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
                        f"— iVote Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[entry.email],
                    fail_silently=False,
                )
                sent += 1
            except Exception:
                failed += 1

        election.emails_sent = True
        election.save(update_fields=['emails_sent'])

        if failed:
            messages.warning(
                request,
                f"Emails sent: {sent}. Failed: {failed}. Check your email settings."
            )
        else:
            messages.success(request, f"Voting invitations sent to {sent} voter(s).")

        return redirect('voting:election_detail', pk=pk)

    roll = election.electoral_roll.all()
    return render(request, 'voting/send_emails.html', {
        'election': election,
        'roll':     roll,
    })


# ─────────────────────────────────────────
# BALLOT HELPERS
# ─────────────────────────────────────────

def _attach_rank_ranges(contests):
    """
    Attach a `rank_range` attribute to each contest (a range object
    from 1 to candidate count) so ranked-choice ballots can render
    a full set of rank options per candidate dropdown.
    """
    for contest in contests:
        contest.rank_range = range(1, contest.candidates.count() + 1)
    return contests


# ─────────────────────────────────────────
# BALLOT (public — no login required)
# ─────────────────────────────────────────

def ballot(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    election = roll.election
    election.sync_status()

    if roll.used:
        return render(request, 'voting/ballot_used.html', {'election': election})
    if election.status == 'closed':
        return render(request, 'voting/ballot_closed.html', {'election': election})
    if election.status == 'pending':
        return render(request, 'voting/ballot_pending.html', {'election': election})

    contests = election.contests.prefetch_related('candidates').all()
    return render(request, 'voting/ballot.html', {
        'roll':     roll,
        'election': election,
        'contests': contests,
    })


# ─────────────────────────────────────────
# SUBMIT VOTE (public — no login required)
# ─────────────────────────────────────────

def submit_vote(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    election = roll.election
    election.sync_status()

    if roll.used:
        return render(request, 'voting/ballot_used.html', {'election': election})
    if election.status != 'active':
        return render(request, 'voting/ballot_closed.html', {'election': election})

    if request.method != 'POST':
        return redirect('voting:ballot', token=token)

    contests = election.contests.prefetch_related('candidates').all()
    errors   = []

    for contest in contests:
        if contest.voting_method == 'plurality':
            # field name: contest_<pk>
            selected = request.POST.getlist(f'contest_{contest.pk}')
            if not selected:
                errors.append(f"Please make a selection for: {contest.title}")
                continue
            if len(selected) > contest.seats:
                errors.append(
                    f"You may select at most {contest.seats} candidate(s) for: {contest.title}"
                )
                continue
            for candidate_pk in selected:
                try:
                    candidate = ContestCandidate.objects.get(
                        pk=candidate_pk, contest=contest
                    )
                    Vote.objects.create(
                        electoral_roll=roll,
                        contest_candidate=candidate,
                        rank=None,
                    )
                except (ContestCandidate.DoesNotExist, IntegrityError):
                    pass

        elif contest.voting_method == 'ranked_choice':
            # fields: rank_<contest_pk>_<candidate_pk> = rank value
            candidates = contest.candidates.all()
            ranked = {}
            for candidate in candidates:
                rank_val = request.POST.get(
                    f'rank_{contest.pk}_{candidate.pk}', ''
                ).strip()
                if rank_val and rank_val.isdigit() and int(rank_val) > 0:
                    ranked[int(rank_val)] = candidate

            if not ranked:
                errors.append(f"Please rank at least one candidate for: {contest.title}")
                continue

            for rank, candidate in ranked.items():
                try:
                    Vote.objects.create(
                        electoral_roll=roll,
                        contest_candidate=candidate,
                        rank=rank,
                    )
                except IntegrityError:
                    pass

    if errors:
        # Roll back any votes saved this session by deleting them
        Vote.objects.filter(electoral_roll=roll).delete()
        contests = _attach_rank_ranges(
            election.contests.prefetch_related('candidates').all()
        )
        return render(request, 'voting/ballot.html', {
            'roll':     roll,
            'election': election,
            'contests': contests,
            'errors':   errors,
        })

    # Mark as voted
    roll.used    = True
    roll.used_at = timezone.now()
    roll.save(update_fields=['used', 'used_at'])

    return redirect('voting:vote_receipt', token=token)


# ─────────────────────────────────────────
# VOTE RECEIPT (public — no login required)
# ─────────────────────────────────────────

def vote_receipt(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    if not roll.used:
        return redirect('voting:ballot', token=token)
    return render(request, 'voting/vote_receipt.html', {
        'roll':     roll,
        'election': roll.election,
    })

