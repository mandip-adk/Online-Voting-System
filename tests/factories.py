"""
factories.py — Factory Boy factories for iVote
Place this file at: tests/factories.py
"""
import uuid
import factory
from django.utils import timezone
from django.contrib.auth import get_user_model

from voting.models import Election, Candidate, VoterParticipation, Votes
from audit.models import AuditRequest

User = get_user_model()


# ------------------------------------------------------------------ #
#  USER FACTORIES
# ------------------------------------------------------------------ #

class VoterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
         

    username   = factory.Sequence(lambda n: f'voter_{n}')
    first_name = factory.Faker('first_name')
    last_name  = factory.Faker('last_name')
    email      = factory.Sequence(lambda n: f'voter_{n}@school.edu')
    voter_id   = factory.Sequence(lambda n: f'SCH{n:05d}')
    role       = 'voter'
    password   = factory.PostGenerationMethodCall('set_password', 'Test@1234')


class OrganizerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        

    username   = factory.Sequence(lambda n: f'organizer_{n}')
    first_name = factory.Faker('first_name')
    last_name  = factory.Faker('last_name')
    email      = factory.Sequence(lambda n: f'organizer_{n}@school.edu')
    voter_id   = factory.Sequence(lambda n: f'ORG{n:05d}')
    role       = 'organizer'
    password   = factory.PostGenerationMethodCall('set_password', 'Test@1234')


# ------------------------------------------------------------------ #
#  ELECTION FACTORIES
# ------------------------------------------------------------------ #

class OpenElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election

    title            = factory.Sequence(lambda n: f'Open Election {n}')
    start_date       = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=1))
    end_date         = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=6))
    status           = 'active'
    created_by       = factory.SubFactory(OrganizerFactory)
    eligibility_type = 'open'
    eligibility_value = ''


class DomainElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election

    title             = factory.Sequence(lambda n: f'Domain Election {n}')
    start_date        = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=1))
    end_date          = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=6))
    status            = 'active'
    created_by        = factory.SubFactory(OrganizerFactory)
    eligibility_type  = 'domain'
    eligibility_value = 'school.edu'


class IDListElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election

    title             = factory.Sequence(lambda n: f'ID List Election {n}')
    start_date        = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=1))
    end_date          = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=6))
    status            = 'active'
    created_by        = factory.SubFactory(OrganizerFactory)
    eligibility_type  = 'id_list'
    eligibility_value = 'SCH00001,SCH00002,SCH00003'


class PendingElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election

    title             = factory.Sequence(lambda n: f'Pending Election {n}')
    start_date        = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=5))
    end_date          = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=12))
    status            = 'pending'
    created_by        = factory.SubFactory(OrganizerFactory)
    eligibility_type  = 'open'
    eligibility_value = ''


class ClosedElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Election

    title             = factory.Sequence(lambda n: f'Closed Election {n}')
    start_date        = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=10))
    end_date          = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=3))
    status            = 'closed'
    created_by        = factory.SubFactory(OrganizerFactory)
    eligibility_type  = 'open'
    eligibility_value = ''


# ------------------------------------------------------------------ #
#  CANDIDATE FACTORY
# ------------------------------------------------------------------ #

class CandidateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Candidate

    user     = factory.SubFactory(VoterFactory)
    election = factory.SubFactory(OpenElectionFactory)
    bio      = factory.Faker('paragraph')
    status   = 'approved'


# ------------------------------------------------------------------ #
#  VOTE FACTORIES
# ------------------------------------------------------------------ #

class VoterParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VoterParticipation

    user     = factory.SubFactory(VoterFactory)
    election = factory.SubFactory(OpenElectionFactory)
    voted_at = factory.LazyFunction(timezone.now)


class VotesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Votes

    token     = factory.LazyFunction(uuid.uuid4)
    election  = factory.SubFactory(OpenElectionFactory)
    candidate = factory.SubFactory(CandidateFactory)
    voted_at  = factory.LazyFunction(timezone.now)


# ------------------------------------------------------------------ #
#  AUDIT FACTORY
# ------------------------------------------------------------------ #

class AuditRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditRequest

    candidate      = factory.SubFactory(CandidateFactory)
    election       = factory.LazyAttribute(lambda o: o.candidate.election)
    reason         = factory.Faker('paragraph')
    status         = 'pending'
    admin_response = None

