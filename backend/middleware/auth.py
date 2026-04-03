"""Bearer token authentication as a FastAPI dependency."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request


def get_auth_checker(api_key: str):
    """Return a dependency that validates the Bearer token.

    If *api_key* is empty, authentication is disabled and the dependency
    is a no-op.
    """

    async def _check_auth(request: Request) -> None:
        if not api_key:
            return

        auth_header = request.headers.get("authorization", "")
        expected = f"Bearer {api_key}"

        if auth_header != expected:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "message": "Invalid or missing API key",
                        "type": "authentication_error",
                        "code": "authentication_error",
                    }
                },
            )

    return _check_auth
