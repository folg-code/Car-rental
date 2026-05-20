from django.urls import path

from apps.accounts.views import AccountLoginView, AccountLogoutView

app_name = "accounts"

urlpatterns = [
    path("logowanie/", AccountLoginView.as_view(), name="login"),
    path("wylogowanie/", AccountLogoutView.as_view(), name="logout"),
]
