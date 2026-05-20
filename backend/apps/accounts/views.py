from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy

from apps.accounts.models import User


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        user = self.request.user
        if isinstance(user, User) and user.is_staff_member:
            return reverse("dashboard:home")
        return reverse("home")


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy("home")
