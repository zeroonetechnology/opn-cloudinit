import secrets
import base64
import string
import bcrypt
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_ssh_public_key

class credentials:
    def __init__(self) -> None:
        pass

    def generate_password(public_key: str) -> tuple[str, str]:

        # Generate a (quasi) cryptographically-secure password
        password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16))

        # Encode password with utf-8 and generate a bcrypt encoded version
        password_utf8 = password.encode()
        password_bcrypt = bcrypt.hashpw(password_utf8,bcrypt.gensalt())

        # Encrypt password against our SSH public key
        key = load_ssh_public_key(public_key.encode('utf-8'),backends.default_backend())
        enc_key = key.encrypt(
        password_utf8,
        padding.PKCS1v15()
        )
        password_enc = base64.b64encode(enc_key)
        print(f"Password (encrypted): f{password_enc.decode()}")
        # Return our bcrypt and ssh encoded passwords
        return password_bcrypt.decode(), password_enc
    