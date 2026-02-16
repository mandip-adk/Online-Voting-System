from django.urls import path
from . import views 
from .views import login_page, dashboard, admin_dashboard, logout_view, register, admin_voters, admin_candidates, admin_elections, admin_results

urlpatterns = [
    # auth
    path("login/", views.login_page, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # dashboards
    path("dashboard/voter/", views.voter_dashboard, name="voter_dashboard"),
    path("dashboard/candidate/", views.candidate_dashboard, name="candidate_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),

    # admin management
    path("admin/voters/", views.admin_voters, name="admin_voters"),
    path("admin/candidates/", views.admin_candidates, name="admin_candidates"),
    path("admin/elections/", views.admin_elections, name="admin_elections"),
    path("admin/results/", views.admin_results, name="admin_results"),

    # admin actions
    path("admin/voters/approve/<int:profile_id>/", views.approve_voter, name="approve_voter"),
    path("admin/voters/block/<int:profile_id>/", views.block_voter, name="block_voter"),
]
