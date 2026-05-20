from django.db.models import QuerySet

from apps.accounts.models import STAFF_ROLES, User


def get_user_by_id(user_id: int) -> User | None:
    return User.objects.filter(pk=user_id).first()


def list_staff_users() -> QuerySet[User]:
    return User.objects.filter(role__in=STAFF_ROLES, is_active=True).order_by(
        "username"
    )


def list_users_by_role(role: str) -> QuerySet[User]:
    return User.objects.filter(role=role, is_active=True).order_by("username")
