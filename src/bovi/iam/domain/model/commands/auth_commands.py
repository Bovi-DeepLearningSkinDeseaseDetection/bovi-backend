from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignUpCommand:
    name: str
    email: str
    password: str
    consent_accepted: bool


@dataclass(frozen=True, slots=True, repr=False)
class SignInCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True, repr=False)
class RefreshSessionCommand:
    refresh_token: str
