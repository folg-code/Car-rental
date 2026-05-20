from apps.accounts.models import User, UserRole


class UserService:
    @staticmethod
    def create_user(
        *,
        username: str,
        password: str,
        role: str,
        email: str = "",
        first_name: str = "",
        last_name: str = "",
        is_staff: bool | None = None,
        is_superuser: bool = False,
    ) -> User:
        if role not in UserRole.values:
            msg = f"Invalid role: {role}"
            raise ValueError(msg)

        staff_roles = {UserRole.OWNER, UserRole.MANAGER}
        resolved_is_staff = is_staff if is_staff is not None else role in staff_roles

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_staff=resolved_is_staff,
            is_superuser=is_superuser,
        )
        return user

    @staticmethod
    def deactivate(user: User) -> User:
        user.is_active = False
        user.save(update_fields=["is_active"])
        return user

    @staticmethod
    def change_role(user: User, role: str) -> User:
        if role not in UserRole.values:
            msg = f"Invalid role: {role}"
            raise ValueError(msg)
        user.role = role
        if role in {UserRole.OWNER, UserRole.MANAGER}:
            user.is_staff = True
        user.save(update_fields=["role", "is_staff"])
        return user
