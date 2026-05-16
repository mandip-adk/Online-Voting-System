import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from voting.models import Candidate, Election, Votes, VoterParticipation

User = get_user_model()

# ------------------------------------------------------------------ #
#  DATA POOLS
# ------------------------------------------------------------------ #
FIRST_NAMES = [
    'Aayush','Mandip','Priya','Bikash','Sunita','Deepak','Anita','Suresh',
    'Kabita','Roshan','Laxmi','Nabin','Sanjay','Pooja','Rajesh','Nisha',
    'Amit','Suman','Gita','Hari','Sita','Ram','Krishna','Devi','Puja',
    'Binod','Sabina','Rajan','Mina','Prakash','Sarita','Dipesh','Anjali',
    'Suraj','Rekha','Bibek','Shristi','Nirmal','Poonam','Manoj',
]

LAST_NAMES = [
    'Nepal','Adhikari','Thapa','Rai','Karki','Gurung','Magar','Tamang',
    'Shrestha','Poudel','Basnet','Koirala','Sharma','Devi','Bahadur',
    'Limbu','Sherpa','Chhetri','Pandey','Ghimire','Oli','Dahal','Bhandari',
    'Subedi','Khadka','Budhathoki','Regmi','Acharya','Bhattarai','Joshi',
]

BIOS = [
    "Passionate about student welfare and dedicated to making a real difference.",
    "Experienced leader with a proven track record in community organizing.",
    "Committed to transparency, fairness, and inclusive decision-making.",
    "Energetic and innovative — ready to bring fresh ideas to the table.",
    "Strong communicator focused on bridging gaps between students and administration.",
    "Advocating for equal opportunities and a better future for everyone.",
    "Believes in data-driven decisions and open governance.",
    "Focused on building a stronger, more connected community.",
]


def random_name():
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


class Command(BaseCommand):
    help = 'Seed the database with 1,000 voters + elections + candidates + votes for iVote'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing non-superuser data before seeding',
        )
        parser.add_argument(
            '--voters',
            type=int,
            default=1000,
            help='Number of voters to create (default: 1000)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Votes.objects.all().delete()
            VoterParticipation.objects.all().delete()
            Candidate.objects.all().delete()
            Election.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Done.\n'))

        self.stdout.write(self.style.MIGRATE_HEADING('=== iVote Seeder Starting ===\n'))

        now = timezone.now()
        voter_count = options['voters']

        # ------------------------------------------------------------------ #
        #  1. ORGANIZERS
        # ------------------------------------------------------------------ #
        self.stdout.write('Creating organizers...')

        organizers_data = [
            {'username': 'organizer_ram',  'first_name': 'Ram',  'last_name': 'Sharma',  'email': 'ram@school.edu',   'voter_id': 'ORG001'},
            {'username': 'organizer_sita', 'first_name': 'Sita', 'last_name': 'Devi',    'email': 'sita@office.com',  'voter_id': 'ORG002'},
            {'username': 'organizer_hari', 'first_name': 'Hari', 'last_name': 'Bahadur', 'email': 'hari@college.edu', 'voter_id': 'ORG003'},
        ]

        organizers = []
        for data in organizers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'role': 'organizer'}
            )
            if created:
                user.set_password('Demo@1234')
                user.save()
            organizers.append(user)
            self.stdout.write(f"  {'Created' if created else 'Exists'}: {user.username}")

        # ------------------------------------------------------------------ #
        #  2. BULK CREATE 1,000 VOTERS
        # ------------------------------------------------------------------ #
        self.stdout.write(f'\nCreating {voter_count} voters...')

        existing_count = User.objects.filter(role='voter').count()
        to_create = voter_count - existing_count

        if to_create <= 0:
            self.stdout.write(f'  Already have {existing_count} voters, skipping.')
        else:
            # Domain split: 40% school.edu | 30% office.com | 30% gmail.com
            school_count = int(to_create * 0.40)
            office_count = int(to_create * 0.30)
            gmail_count  = to_create - school_count - office_count

            new_users = []
            used_voter_ids = set(User.objects.values_list('voter_id', flat=True))
            used_usernames = set(User.objects.values_list('username', flat=True))

            def make_voter(index, domain, prefix):
                voter_id = f'{prefix}{index:05d}'
                while voter_id in used_voter_ids:
                    index += 1
                    voter_id = f'{prefix}{index:05d}'
                used_voter_ids.add(voter_id)

                first, last = random_name()
                base_username = f'{first.lower()}_{last.lower()}_{index}'
                username = base_username
                counter = 1
                while username in used_usernames:
                    username = f'{base_username}_{counter}'
                    counter += 1
                used_usernames.add(username)

                return User(
                    username=username,
                    first_name=first,
                    last_name=last,
                    email=f'{username}@{domain}',
                    voter_id=voter_id,
                    role='voter',
                )

            idx = existing_count + 1
            for i in range(school_count):
                new_users.append(make_voter(idx + i, 'school.edu', 'SCH'))
            idx += school_count
            for i in range(office_count):
                new_users.append(make_voter(idx + i, 'office.com', 'OFF'))
            idx += office_count
            for i in range(gmail_count):
                new_users.append(make_voter(idx + i, 'gmail.com', 'GEN'))

            from django.contrib.auth.hashers import make_password
            hashed = make_password('Demo@1234')
            for u in new_users:
                u.password = hashed

            User.objects.bulk_create(new_users, batch_size=200, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'  {len(new_users)} voters created via bulk_create.'))

        # Reload all voters split by domain
        all_voters    = list(User.objects.filter(role='voter'))
        school_voters = [v for v in all_voters if v.email.endswith('@school.edu')]
        office_voters = [v for v in all_voters if v.email.endswith('@office.com')]
        gmail_voters  = [v for v in all_voters if v.email.endswith('@gmail.com')]

        self.stdout.write(f'  school.edu : {len(school_voters)} voters')
        self.stdout.write(f'  office.com : {len(office_voters)} voters')
        self.stdout.write(f'  gmail.com  : {len(gmail_voters)} voters')

        # ------------------------------------------------------------------ #
        #  3. ELECTIONS
        # ------------------------------------------------------------------ #
        self.stdout.write('\nCreating elections...')

        # Build id_list from random sample of voter IDs
        voters_with_ids = [v for v in all_voters if v.voter_id]
        id_list_sample = ','.join(
            v.voter_id for v in random.sample(voters_with_ids, min(300, len(voters_with_ids)))
        )

        elections_data = [
            # CLOSED
            {
                'title':            'School President Election 2024',
                'start_date':       now - timedelta(days=60),
                'end_date':         now - timedelta(days=53),
                'status':           'closed',
                'created_by':       organizers[0],
                'eligibility_type': 'domain',
                'eligibility_value':'school.edu',
            },
            {
                'title':            'Office Representative Poll 2024',
                'start_date':       now - timedelta(days=30),
                'end_date':         now - timedelta(days=23),
                'status':           'closed',
                'created_by':       organizers[1],
                'eligibility_type': 'open',
                'eligibility_value':'',
            },
            # ACTIVE
            {
                'title':            'College Cultural Committee Vote',
                'start_date':       now - timedelta(days=1),
                'end_date':         now + timedelta(days=6),
                'status':           'active',
                'created_by':       organizers[2],
                'eligibility_type': 'open',
                'eligibility_value':'',
            },
            {
                'title':            'Best Staff of the Year 2025',
                'start_date':       now - timedelta(hours=5),
                'end_date':         now + timedelta(days=3),
                'status':           'active',
                'created_by':       organizers[1],
                'eligibility_type': 'id_list',
                'eligibility_value': id_list_sample,
            },
            # PENDING
            {
                'title':            'Student Union Election 2025',
                'start_date':       now + timedelta(days=5),
                'end_date':         now + timedelta(days=12),
                'status':           'pending',
                'created_by':       organizers[0],
                'eligibility_type': 'domain',
                'eligibility_value':'school.edu',
            },
            {
                'title':            'Annual Tech Club Leadership Vote',
                'start_date':       now + timedelta(days=10),
                'end_date':         now + timedelta(days=17),
                'status':           'pending',
                'created_by':       organizers[2],
                'eligibility_type': 'open',
                'eligibility_value':'',
            },
        ]

        elections = []
        for data in elections_data:
            election, created = Election.objects.get_or_create(
                title=data['title'],
                defaults=data,
            )
            elections.append(election)
            self.stdout.write(
                f"  {'Created' if created else 'Exists'}: \"{election.title}\" [{election.status}]"
            )

        # ------------------------------------------------------------------ #
        #  4. CANDIDATES
        # ------------------------------------------------------------------ #
        self.stdout.write('\nCreating candidates...')

        def make_candidate(election, user, status):
            candidate, _ = Candidate.objects.get_or_create(
                election=election,
                user=user,
                defaults={'bio': random.choice(BIOS), 'status': status}
            )
            return candidate

        random.shuffle(school_voters)
        random.shuffle(office_voters)
        random.shuffle(gmail_voters)

        e0_candidates = [make_candidate(elections[0], v, 'approved') for v in school_voters[:4]]
        e1_candidates = [make_candidate(elections[1], v, 'approved') for v in office_voters[:3]]
        e2_candidates = [make_candidate(elections[2], v, 'approved') for v in gmail_voters[:4]]
        e3_candidates = [make_candidate(elections[3], v, 'approved') for v in office_voters[3:6]]
        [make_candidate(elections[4], v, 'approved') for v in school_voters[4:7]]
        [make_candidate(elections[4], v, 'pending')  for v in school_voters[7:9]]
        [make_candidate(elections[5], v, 'approved') for v in gmail_voters[4:7]]

        self.stdout.write(self.style.SUCCESS(f'  {Candidate.objects.count()} candidates total'))

        # ------------------------------------------------------------------ #
        #  5. BULK CAST VOTES
        # ------------------------------------------------------------------ #
        self.stdout.write('\nCasting votes...')

        def bulk_cast_votes(election, voter_pool, candidate_list, vote_ratio=0.75):
            if not candidate_list:
                return 0

            already_voted = set(
                VoterParticipation.objects.filter(election=election)
                .values_list('user_id', flat=True)
            )
            eligible = [v for v in voter_pool if v.id not in already_voted]
            voters_who_vote = random.sample(eligible, int(len(eligible) * vote_ratio))

            if not voters_who_vote:
                return 0

            participations = []
            votes = []

            for voter in voters_who_vote:
                chosen   = random.choice(candidate_list)
                voted_at = now - timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                )
                participations.append(
                    VoterParticipation(user=voter, election=election, voted_at=voted_at)
                )
                votes.append(
                    Votes(election=election, candidate=chosen, token=uuid.uuid4(), voted_at=voted_at)
                )

            VoterParticipation.objects.bulk_create(participations, batch_size=500, ignore_conflicts=True)
            Votes.objects.bulk_create(votes, batch_size=500, ignore_conflicts=True)
            return len(votes)

        v0 = bulk_cast_votes(elections[0], school_voters, e0_candidates, 0.85)
        v1 = bulk_cast_votes(elections[1], school_voters + office_voters + gmail_voters[:100], e1_candidates, 0.70)
        v2 = bulk_cast_votes(elections[2], gmail_voters,  e2_candidates, 0.60)
        v3 = bulk_cast_votes(elections[3], office_voters + gmail_voters[:100], e3_candidates, 0.55)

        self.stdout.write(f'  Election 0 (closed, school domain) — {v0} votes')
        self.stdout.write(f'  Election 1 (closed, open)          — {v1} votes')
        self.stdout.write(f'  Election 2 (active, open)          — {v2} votes')
        self.stdout.write(f'  Election 3 (active, id_list)       — {v3} votes')

        # ------------------------------------------------------------------ #
        #  6. SUMMARY
        # ------------------------------------------------------------------ #
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('=== Seed Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'  Organizers         : {User.objects.filter(role="organizer").count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Voters             : {User.objects.filter(role="voter").count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Elections          : {Election.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Candidates         : {Candidate.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  VoterParticipation : {VoterParticipation.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Votes cast         : {Votes.objects.count()}'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('All seeded user passwords: Demo@1234'))
        self.stdout.write('Organizers: organizer_ram / organizer_sita / organizer_hari')
        self.stdout.write('')

