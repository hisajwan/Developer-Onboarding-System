from app.domain.ports import PasswordHasher
from app.infrastructure.auth.passwords import (
    BcryptPasswordHasher,
    dummy_password_hash,
    hash_password,
    verify_password,
)


def test_a_correct_password_verifies() -> None:
    assert verify_password("s3cret", hash_password("s3cret"))


def test_a_wrong_password_does_not_verify() -> None:
    assert not verify_password("wrong", hash_password("s3cret"))


def test_the_same_password_hashes_differently_each_time() -> None:
    assert hash_password("s3cret") != hash_password("s3cret")  # bcrypt salts every hash


def test_dummy_hash_is_stable_within_a_process_and_never_verifies() -> None:
    assert dummy_password_hash() == dummy_password_hash()
    assert not verify_password("whatever", dummy_password_hash())


def test_the_bcrypt_adapter_satisfies_the_port() -> None:
    hasher = BcryptPasswordHasher()

    assert isinstance(hasher, PasswordHasher)
    assert hasher.verify("s3cret", hasher.hash("s3cret"))
    assert not hasher.verify("whatever", hasher.dummy_hash())
