from fastapi import Response

from orcestr_auth import AuthConfig, CookieConfig
from orcestr_auth.cookies import clear_auth_cookies, set_auth_cookies


def test_cookie_set_and_delete_attributes_are_symmetric() -> None:
    config = AuthConfig(
        secret_key="secret",
        cookie=CookieConfig(
            access_name="access",
            refresh_name="refresh",
            secure=True,
            same_site="strict",
            domain=".example.com",
            path="/api",
        ),
    )
    response = Response()
    set_auth_cookies(response, "access-token", "refresh-token", config)
    set_headers = response.headers.getlist("set-cookie")
    assert len(set_headers) == 2
    assert all("HttpOnly" in header for header in set_headers)
    assert all("Secure" in header for header in set_headers)
    assert all("SameSite=strict" in header for header in set_headers)
    assert all("Path=/api" in header for header in set_headers)
    assert all("Domain=.example.com" in header for header in set_headers)

    cleared = Response()
    clear_auth_cookies(cleared, config)
    clear_headers = cleared.headers.getlist("set-cookie")
    assert len(clear_headers) == 2
    assert all("Max-Age=0" in header for header in clear_headers)
    assert all("Path=/api" in header for header in clear_headers)
    assert all("Domain=.example.com" in header for header in clear_headers)
