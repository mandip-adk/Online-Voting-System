from django.urls import path
from . import views 
from .views import login_page, dashboard, admin_dashboard, logout_view, register, admin_voters, admin_candidates, admin_elections, admin_results

urlpatterns=[
    path("register/", register, name="register"),
    path("login/", login_page, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("logout/", logout_view, name="logout"),
    
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/voters/", admin_voters, name="admin_voters"),
    path("admin/candidates/", admin_candidates, name="admin_candidates"),
    path("admin/results/", admin_results, name="admin_results"),
    path("admin/elections/", admin_elections, name= "admin_elections")
    
]