from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from apps.accounts.models import STAFF_ROLES, User, UserRole


def user_has_role(user: User, *roles: str) -> bool:
    return user.is_authenticated and user.role in roles


def staff_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @login_required
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = request.user
        if not isinstance(user, User) or user.role not in STAFF_ROLES:
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(
    *roles: str,
) -> Callable[[Callable[..., HttpResponse]], Callable[..., HttpResponse]]:
    allowed = set(roles)

    def decorator(
        view_func: Callable[..., HttpResponse],
    ) -> Callable[..., HttpResponse]:
        @login_required
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            user = request.user
            if not isinstance(user, User) or user.role not in allowed:
                return redirect("accounts:login")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def owner_or_manager_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    return role_required(UserRole.OWNER, UserRole.MANAGER)(view_func)


def customer_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    return role_required(UserRole.CUSTOMER)(view_func)
