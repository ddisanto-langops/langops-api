import os
import jwt
from fastapi import HTTPException, status, Request

CF_TEAM_URL = os.getenv("CF_TEAM_URL")
TRUSTED_AUDIENCES = os.getenv("TRUSTED_AUDIENCES")
CERTS_URL = f"{CF_TEAM_URL}/cdn-cgi/access/certs"

jwks_client = jwt.PyJWKClient(CERTS_URL)


def get_trusted_audiences(audiences: str) -> list[str]:
    """Compiles a list of trusted audience tokens, filtering out empty variables.
    Expected audiences format: TRUSTED_AUDIENCES="aud1,aud2,aud3"
    """
    return [aud.strip() for aud in audiences.split(",") if aud]


async def verify_jwt(request: Request) -> dict:
    """
    Extracts and cryptographically verifies the automatic CF_Authorization JWT.
    """
    
    token = request.headers.get("cf-authorization") or request.headers.get("cf_authorization")
    
    try:
        audiences = get_trusted_audiences(TRUSTED_AUDIENCES)
        if not audiences:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail= "Target audience missing or not in listed of trusted audiences"
            )
        
        target_audience = audiences[0] if len(audiences) == 1 else audiences
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=target_audience,
            issuer=CF_TEAM_URL,
            options={
                "require": ["aud"]
            }
        )

        request.state.user_email = payload.get("email", "unknown")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience is missing or untrusted.")