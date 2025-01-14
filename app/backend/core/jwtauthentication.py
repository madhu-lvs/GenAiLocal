from datetime import datetime, timedelta
import os
import jwt

class JWTManager:
    """
    JWTManager is responsible for generating and decoding JWT tokens using a secret key. 
    It provides methods to create tokens with embedded identity and role information, 
    and to decode tokens while handling common errors such as expiration or invalid tokens.
    """
    
    def __init__(self):
        """
        Initializes the JWTManager with a secret key.
        
        The secret key is retrieved from the environment variable `SECRET_KEY`. This 
        key is used to sign the JWT tokens and later verify them during decoding.
        
        Raises:
            ValueError: If the secret key is not set.
        """
        self.secret_key = os.getenv("SECRET_KEY", "")
        if not self.secret_key:
            raise ValueError("SECRET_KEY environment variable is not set.")
    
    def generate_jwt(self, identity: str, role: str) -> str:
        """
        Generates a JWT token with identity and role information.
        
        This method creates a JWT token that includes the user's identity and role, as 
        well as the issue time (`iat`) and expiration time (`exp`). The token is signed 
        with the secret key using the HS256 algorithm.
        
        Args:
            identity (str): The identity of the user (e.g., username, email).
            role (str): The role of the user (e.g., admin, user).

        Returns:
            str: The generated JWT token encoded as a string.
        """
        payload = {
            "identity": identity,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def decode_jwt(self, token: str) -> dict:
        """
        Decodes a JWT token and returns its payload.
        
        This method attempts to decode the provided JWT token using the secret key. 
        It handles common errors such as token expiration or invalid signatures. If 
        the token is valid, it returns the payload containing the identity and role.
        
        Args:
            token (str): The JWT token to be decoded.
        
        Returns:
            dict: The decoded payload if the token is valid, or a message indicating 
            an error if the token is expired or invalid.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return {"msg": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"msg": "Invalid token"}
