import httpx

from app.core.config import settings


class AuthKitError(Exception):
    pass


async def get_current_user_id(token: str) -> str:
    """
    Calls AuthKit's /me endpoint to validate the token.
    Returns the user's UUID (used as user_id in PriceRadar).
    Raises AuthKitError if the token is invalid or AuhtKit is unreachable.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTHKIT_URL}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
    except httpx.RequestError as e:
        raise AuthKitError(f"Authkit is unreachable: {e}")
    
    if response.status_code == 401:
        raise AuthKitError("Invalid or expired token")
    
    if response.status_code != 200:
        raise AuthKitError(f"AuthKit returned unexpected status: {response.status_code}")
    
    data = response.json()
    return data["id"]