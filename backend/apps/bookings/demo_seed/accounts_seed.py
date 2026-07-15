"""Konta panelu i portalu klienta dla demo."""

from __future__ import annotations

from apps.accounts.models import User, UserRole
from apps.accounts.services.user import UserService
from apps.bookings.demo_seed.catalog import (
    DEMO_CUSTOMER_PASSWORD,
    DEMO_CUSTOMER_USERNAME,
    DEMO_MANAGER_EMAIL,
    DEMO_MANAGER_PASSWORD,
    DEMO_MANAGER_USERNAME,
    demo_note,
)
from apps.bookings.models import Customer


def seed_staff_user() -> User:
    user = User.objects.filter(username=DEMO_MANAGER_USERNAME).first()
    if user is None:
        return UserService.create_user(
            username=DEMO_MANAGER_USERNAME,
            password=DEMO_MANAGER_PASSWORD,
            role=UserRole.MANAGER,
            email=DEMO_MANAGER_EMAIL,
            first_name="Demo",
            last_name="Kierownik",
            is_staff=True,
            is_superuser=False,
        )
    user.email = DEMO_MANAGER_EMAIL
    user.first_name = "Demo"
    user.last_name = "Kierownik"
    user.role = UserRole.MANAGER
    user.is_staff = True
    user.is_superuser = False
    user.is_active = True
    user.set_password(DEMO_MANAGER_PASSWORD)
    user.save()
    return user


def link_portal_customer(customer: Customer) -> User:
    if customer.user_id is not None:
        user = customer.user
        user.set_password(DEMO_CUSTOMER_PASSWORD)
        user.save()
        return user

    user = User.objects.filter(username=DEMO_CUSTOMER_USERNAME).first()
    if user is None:
        user = UserService.create_user(
            username=DEMO_CUSTOMER_USERNAME,
            password=DEMO_CUSTOMER_PASSWORD,
            role=UserRole.CUSTOMER,
            email=customer.email or f"{DEMO_CUSTOMER_USERNAME}@demo.pl",
            first_name=customer.first_name,
            last_name=customer.last_name,
            is_staff=False,
            is_superuser=False,
        )
    else:
        user.role = UserRole.CUSTOMER
        user.email = customer.email or user.email
        user.first_name = customer.first_name
        user.last_name = customer.last_name
        user.is_active = True
        user.set_password(DEMO_CUSTOMER_PASSWORD)
        user.save()

    customer.user = user
    customer.notes = demo_note("portal-customer")
    customer.save(update_fields=["user", "notes", "updated_at"])
    return user
