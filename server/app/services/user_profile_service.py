from dataclasses import replace

from app.core.exceptions import InvalidCredentialsError, NotFoundError
from app.domain.models import User
from app.domain.ports import PasswordHasher, UserRegistry


class UserProfileService:
    """What a logged-in user can do to their own account: edit their name, change their password.

    Username and email are not editable here - changing either is out of scope for this feature.
    """

    def __init__(self, users: UserRegistry, passwords: PasswordHasher) -> None:
        self._users = users
        self._passwords = passwords

    async def get_profile(self, username: str) -> User:
        user = await self._users.get(username)
        if user is None:
            raise NotFoundError("Account not found.")
        return user

    async def update_profile(self, username: str, first_name: str, last_name: str) -> User:
        user = await self.get_profile(username)
        updated = replace(user, first_name=first_name, last_name=last_name)
        await self._users.record(updated)
        return updated

    async def change_password(
        self, username: str, current_password: str, new_password: str
    ) -> None:
        user = await self.get_profile(username)
        if not self._passwords.verify(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect.")
        await self._users.record(replace(user, password_hash=self._passwords.hash(new_password)))
