import os
import jwt
from fastapi import Depends, HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader

cloudflare_token_scheme = APIKeyHeader(name="CF_Authorization", auto_error=True)

CF_TEAM_URL = os.getenv("CF_TEAM_URL")
TRUSTED_AUDIENCES = [
    os.getenv("API_AUD_TAG"),
    os.getenv("LANGOPS_WEBSITE_AUD_TAG")
]
CERTS_URL = f"{CF_TEAM_URL}/cdn-cgi/access/certs"

jwks_client = jwt.PyJWKClient(CERTS_URL)


def get_trusted_audiences() -> list[str]:
    """Compiles a list of live audience tokens, filtering out empty variables."""
    return [aud for aud in TRUSTED_AUDIENCES if aud]


async def verify_jwt(request: Request, token: str = Depends(cloudflare_token_scheme)) -> dict:
    """
    Extracts and cryptographically verifies the automatic CF_Authorization JWT.
    """
    
    try:
        audiences = get_trusted_audiences()
        if not audiences:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail= "Target audience missing or not in listed of trusted audiences"
            )
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audiences,
            issuer=CF_TEAM_URL
        )

        request.state.user_email = payload.get("email", "unknown")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience is untrusted or mismatched.")