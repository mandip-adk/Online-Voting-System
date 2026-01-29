from django.urls import path
from . import views 
from .views import login_page, dashboard, admin_dashboard, logout_view, register

urlpatterns=[
    path("register/", register, name="register"),
    path("login/", login_page, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("admin_dashboard/", admin_dashboard, name="admin_dashboard"),
    path("logout/", logout_view, name="logout"),
    
]