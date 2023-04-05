from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class Auth0Response(BaseModel):
    iss: str
    sub: str
    aud: str
    iat: int
    exp: int
    azp: str
    gty: str
