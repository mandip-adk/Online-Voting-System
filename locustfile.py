"""
iVote — Locust Load & Performance Test
=======================================
Run with:
    locust -f locustfile.py --host=http://127.0.0.1:8000

Then open: http://localhost:8089
"""

import random
from locust import HttpUser, task, between


# ------------------------------------------------------------------ #
#  ACTUAL URLs (verified from manage.py shell)
# ------------------------------------------------------------------ #
# /accounts/login/          — login page
# /accounts/register/       — register page
# /voter/dashboard/         — voter dashboard
# /organizer/dashboard/     — organizer dashboard
# /voting/                  — election list
# /voting/election/<id>/    — election detail
# /voting/election/<id>/results/ — results
# /audit/requests/          — audit list


ORGANIZER_ACCOUNTS = [
    {"username": "organizer_ram",  "password": "Demo@1234"},
    {"username": "organizer_sita", "password": "Demo@1234"},
    {"username": "organizer_hari", "password": "Demo@1234"},
]

ELECTION_IDS = [1, 2, 3, 4, 5, 6]


def get_csrf_token(client):
    """Fetch login page to get CSRF token from cookies."""
    client.get("/accounts/login/", name="/accounts/login/ [csrf fetch]")
    return client.cookies.get("csrftoken", "")


# ------------------------------------------------------------------ #
#  VOTER USER
# ------------------------------------------------------------------ #

class VoterUser(HttpUser):
    weight    = 7
    wait_time = between(2, 6)

    def on_start(self):
        creds = random.choice(ORGANIZER_ACCOUNTS)
        self.login(creds["username"], creds["password"])

    def login(self, username, password):
        csrf = get_csrf_token(self.client)
        self.client.post(
            "/accounts/login/",
            data={
                "username":            username,
                "password":            password,
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": "http://127.0.0.1:8000/accounts/login/"},
            name="/accounts/login/ [POST]",
            allow_redirects=True,
        )

    @task(3)
    def browse_election_list(self):
        self.client.get("/voting/", name="/voting/ [election list]")

    @task(2)
    def view_election_detail(self):
        eid = random.choice(ELECTION_IDS)
        self.client.get(
            f"/voting/election/{eid}/",
            name="/voting/election/[id]/",
        )

    @task(1)
    def view_results(self):
        eid = random.choice(ELECTION_IDS)
        self.client.get(
            f"/voting/election/{eid}/results/",
            name="/voting/election/[id]/results/",
        )

    @task(1)
    def view_dashboard(self):
        self.client.get("/voter/dashboard/", name="/voter/dashboard/")


# ------------------------------------------------------------------ #
#  ORGANIZER USER
# ------------------------------------------------------------------ #

class OrganizerUser(HttpUser):
    weight    = 2
    wait_time = between(3, 8)

    def on_start(self):
        creds = random.choice(ORGANIZER_ACCOUNTS)
        self.login(creds["username"], creds["password"])

    def login(self, username, password):
        csrf = get_csrf_token(self.client)
        self.client.post(
            "/accounts/login/",
            data={
                "username":            username,
                "password":            password,
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": "http://127.0.0.1:8000/accounts/login/"},
            name="/accounts/login/ [organizer POST]",
            allow_redirects=True,
        )

    @task(3)
    def view_organizer_dashboard(self):
        self.client.get("/organizer/dashboard/", name="/organizer/dashboard/")

    @task(2)
    def browse_elections(self):
        self.client.get("/voting/", name="/voting/ [organizer]")

    @task(2)
    def view_election_detail(self):
        eid = random.choice(ELECTION_IDS)
        self.client.get(
            f"/voting/election/{eid}/",
            name="/voting/election/[id]/ [organizer]",
        )

    @task(1)
    def view_audit_requests(self):
        self.client.get("/audit/requests/", name="/audit/requests/")


# ------------------------------------------------------------------ #
#  ANONYMOUS USER
# ------------------------------------------------------------------ #

class AnonymousUser(HttpUser):
    weight    = 1
    wait_time = between(1, 4)

    @task(2)
    def hit_login_page(self):
        self.client.get("/accounts/login/", name="/accounts/login/ [anon]")

    @task(2)
    def hit_register_page(self):
        self.client.get("/accounts/register/", name="/accounts/register/")

    @task(1)
    def hit_election_list_unauthenticated(self):
        """Should redirect to login — tests redirect performance."""
        self.client.get(
            "/voting/",
            name="/voting/ [anon redirect]",
            allow_redirects=False,
        )

        