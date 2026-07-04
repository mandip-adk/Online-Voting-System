from django.urls import path
from .views import (
    election_list, election_detail, create_election,
    edit_election, delete_election,
    add_contest, edit_contest, delete_contest,
    add_candidate, edit_candidate, delete_candidate,
    upload_electoral_roll, voter_participation,
    election_results, send_voting_emails,
    ballot, submit_vote, vote_receipt,
)

app_name = 'voting'

urlpatterns = [
    path('',  election_list,  name='election_list'),
    path('create/',  create_election,  name='create_election'),
    path('<int:pk>/',  election_detail,     name='election_detail'),
    path('<int:pk>/edit/', edit_election,   name='edit_election'),
    path('<int:pk>/delete/', delete_election,  name='delete_election'),

    # Contests
    path('<int:pk>/contests/add/', add_contest, name='add_contest'),
    path('<int:pk>/contests/<int:ck>/edit/', edit_contest, name='edit_contest'),
    path('<int:pk>/contests/<int:ck>/delete/', delete_contest, name='delete_contest'),

    # Candidates
    path('<int:pk>/contests/<int:ck>/candidates/add/', add_candidate,  name='add_candidate'),
    path('<int:pk>/contests/<int:ck>/candidates/<int:cand_pk>/edit/',   edit_candidate,   name='edit_candidate'),
    path('<int:pk>/contests/<int:ck>/candidates/<int:cand_pk>/delete/', delete_candidate, name='delete_candidate'),

    # Electoral roll
    path('<int:pk>/voters/upload/', upload_electoral_roll,  name='upload_electoral_roll'),
    path('<int:pk>/voters/',  voter_participation,    name='voter_participation'),

    # Results & emails
    path('<int:pk>/results/', election_results,       name='election_results'),
    path('<int:pk>/send-emails/',  send_voting_emails,     name='send_voting_emails'),

    # Public ballot (no login)
    path('vote/<uuid:token>/', ballot, name='ballot'),
    path('vote/<uuid:token>/submit/', submit_vote, name='submit_vote'),
    path('vote/<uuid:token>/receipt/',  vote_receipt,  name='vote_receipt'),
]