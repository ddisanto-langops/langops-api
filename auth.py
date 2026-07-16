import os
import jwt
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader

CF_TEAM_URL = os.getenv("CF_TEAM_URL")
TRUSTED_AUDIENCES = os.getenv("TRUSTED_AUDIENCES")
CERTS_URL = f"{CF_TEAM_URL}/cdn-cgi/access/certs"

cf_jwt_header = APIKeyHeader(name="Cf-Access-Jwt-Assertion", auto_error=False)
cf_id_header = APIKeyHeader(name="CF-Access-Client-Id", auto_error=False)
cf_secret_header = APIKeyHeader(name="CF-Access-Client-Secret", auto_error=False)

jwks_client = jwt.PyJWKClient(CERTS_URL) if CF_TEAM_URL else None


def get_trusted_audiences(audiences: str) -> list[str]:
    """Compiles a list of trusted audience tokens, filtering out empty variables.
    Expected audiences format: TRUSTED_AUDIENCES="aud1,aud2,aud3"
    """
    if not audiences: return []
    return [aud.strip() for aud in audiences.split(",") if aud]


async def verify_jwt(
    request: Request, 
    token: str = Depends(cf_jwt_header),
    client_id: str = Depends(cf_id_header),
    client_secret: str = Depends(cf_secret_header)
) -> dict:
    """
    Extracts and cryptographically verifies the automatic CF_Authorization JWT.
    Bypasses validation if ENVIRONMENT is set to DEV.
    """

    accepted_environments = {"DEV", "PROD"}
    environment = os.getenv("ENVIRONMENT")
    if environment not in accepted_environments:
        raise ValueError("Auth error: user must specify either 'DEV' or 'PROD' environment.")
 
    if environment == "DEV":
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing CF-Access-Client-Id or CF-Access-Client-Secret for DEV environment",
            )
        # Mock production behavior
        request.state.user_email = "dev-user@local.internal"
        return {"email": "dev-user@local.internal", "mocked": True}

    # 2. PRODUCTION JWT CHECK
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Cf-Access-Jwt-Assertion header for PROD environment",
        )
    
    try:
        audiences = get_trusted_audiences(TRUSTED_AUDIENCES)
        if not audiences:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Target audience missing or not in listed of trusted audiences"
            )
        
        target_audience = audiences[0] if len(audiences) == 1 else audiences
        
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=target_audience,
            issuer=CF_TEAM_URL,
            options={"require": ["aud"]}
        )

        request.state.user_email = payload.get("email", "unknown")
        return payload
    
    except  jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
    
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer")
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience is missing or untrusted.")