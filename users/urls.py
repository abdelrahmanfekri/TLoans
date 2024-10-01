from django.urls import path
from .views import register_view, login_view, logout_view, protected_route

app_name = "users"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("protected/", protected_route, name="protected"),
]
