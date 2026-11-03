from dataclasses import replace

from app.core.exceptions import InvalidCredentialsError, NotFoundError
from app.domain.models import User
from app.domain.ports import PasswordHasher, UserRegistry
from app.services.project_lifecycle_service import ProjectLifecycleService


class UserProfileService:
    """What a logged-in user can do to their own account: edit their name, change their password,
    delete the account.

    Username and email are not editable here - changing either is out of scope for this feature.
    """

    def __init__(
        self, users: UserRegistry, passwords: PasswordHasher, projects: ProjectLifecycleService
    ) -> None:
        self._users = users
        self._passwords = passwords
        self._projects = projects

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
        user = await self._verified(username, current_password)
        await self._users.record(replace(user, password_hash=self._passwords.hash(new_password)))

    async def delete_account(self, username: str, password: str) -> None:
        """Deletes the account and everything it owns. The password is asked again, so a session
        left open on someone else's screen can't be used to wipe the account."""
        await self._verified(username, password)
        await self._projects.delete_all_content_for(username)
        await self._users.delete(username)

    async def _verified(self, username: str, password: str) -> User:
        user = await self.get_profile(username)
        if not self._passwords.verify(password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect.")
        return user
