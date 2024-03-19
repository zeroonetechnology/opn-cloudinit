import requests
import base64
import secrets
import string
import bcrypt
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_ssh_public_key
from opn_cloudinit.conf.opnsense import opnsense as opnsense_conf
from opn_cloudinit.metadata.metadata import metadata 
from opn_cloudinit.creds.credentials import credentials as creds

opnsense = opnsense_conf()

# Confirm we can reach the endpoint

def main():
    # Add gateway rule to allow access to the metadata endpoint
    opnsense.set_gateway_options()
    # Retrieve the hostname
    hostname = requests.get('http://169.254.169.254/latest/meta-data/hostname').text
    print (f"Hostname: {hostname}")

    # Retrieve the SSH public key
    public_key = requests.get('http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key').text
    print (f"Public key: {public_key}")

    # Generate a (quasi) cryptographically-secure password
    password = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16))
    password_b64 = password.encode('utf-8')
    print(f'Password (plaintext): {password}')

    # Generate bcrypt
    password_bcrypt = bcrypt.hashpw(password_b64,bcrypt.gensalt())
    print(f"Password (bcrypt): {password_bcrypt.decode('utf-8')}")

    # Enccrypt password against our SSH public key
    key = load_ssh_public_key(public_key.encode('utf-8'),backends.default_backend())
    enc_key = key.encrypt(
        password_b64,
        padding.PKCS1v15()
        )
    enc_password = base64.b64encode(enc_key)

    # Post password to our metadata endpoint
    put_pass = requests.post('http://169.254.169.254/openstack/2013-04-04/password',enc_password.decode('utf-8'))
    print (put_pass.status_code)
    print(f"Password (encrypted): f{enc_password.decode('utf-8')}")
    opnsense.set_system_configuration(
        path = "./config.xml",
        password = password_bcrypt.decode('utf-8')
    )