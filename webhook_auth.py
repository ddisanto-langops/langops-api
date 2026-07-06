import os
import json
import requests
import base64
import hashlib
import hmac
import ipaddress


class TrelloWebhook:
    def __init__(self):
        self.callback: str = os.getenv("TRELLO_WEBHOOK_CALLBACK")
        trello_secret: str = os.getenv("TRELLO_SECRET")

        if not self.callback:
            raise Exception({"error": "Missing callback URL. This is required for verification of webhooks."})
        
        if not trello_secret:
            raise Exception({"error": "Missing Trello Secret. This is required for verification of webhooks."})

    
    def verify_signature(self, raw_body: bytes, header_hash: str) -> bool:
        """Check the Trello webhook content and headers against client secret to ensure authenticity
        Args:
            request_body: the Trello webhook
            header_hash: the hash provided by Trello in the X-Trello-Webhook header
        """
        if not header_hash:
            return False
        
        content = raw_body + self.callback.encode("utf-8")
        
        digest = hmac.new(
            os.getenv("TRELLO_SECRET").encode("utf-8"),
            msg=content,
            digestmod=hashlib.sha1
        ).digest()
        
        computed_hash = base64.b64encode(digest).decode("utf-8")

        return hmac.compare_digest(computed_hash, header_hash)


class CrowdinWebhook:
    
    def verify_cf_access(self, provided_id: str, provided_secret: str):
        cf_access_id = os.getenv("API_CF_ID")
        cf_access_secret = os.getenv("API_CF_SECRET")
        
        combined_provided_creds = f"{provided_id}:{provided_secret}"
        provided_creds_encoded = hashlib.sha256(combined_provided_creds.encode("utf-8"))
        hashed_provided_creds = provided_creds_encoded.hexdigest()
        
        combined_creds = f"{cf_access_id}:{cf_access_secret}"
        encoded_creds = hashlib.sha256(combined_creds.encode("utf-8"))
        hashed_creds = encoded_creds.hexdigest()
        
        return hmac.compare_digest(hashed_creds, hashed_provided_creds)
        
        
        
        