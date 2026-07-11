from passlib.context import CryptContext

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def verify_and_update_password(
    password: str,
    password_hash: str,
) -> tuple[bool, str | None]:
    return password_context.verify_and_update(password, password_hash)

