from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UserRole(models.TextChoices):
    OWNER = "owner", "Wlasciciel"
    MANAGER = "manager", "Kierownik"
    EMPLOYEE = "employee", "Pracownik"
    ACCOUNTANT = "accountant", "Ksiegowy"
    CUSTOMER = "customer", "Klient"


STAFF_ROLES = frozenset(
    {
        UserRole.OWNER,
        UserRole.MANAGER,
        UserRole.EMPLOYEE,
        UserRole.ACCOUNTANT,
    }
)


class User(AbstractUser):
    objects = UserManager()

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
    )

    class Meta:
        verbose_name = "uzytkownik"
        verbose_name_plural = "uzytkownicy"

    @property
    def is_staff_member(self) -> bool:
        return self.role in STAFF_ROLES

    @property
    def is_customer_account(self) -> bool:
        return self.role == UserRole.CUSTOMER
