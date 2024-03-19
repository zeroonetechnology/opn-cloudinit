import base64
import time
from os import path
from opn_cloudinit.conf.opnsense import opnsense as opnsense_conf
from opn_cloudinit.metadata.metadata import metadata as metadata
from opn_cloudinit.creds.credentials import credentials as credentials

opnsense = opnsense_conf()
meta = metadata()
creds = credentials()


def main():
    
    # Check if config has already completed
    if path.exists('./metadata.txt') == True:
        print("Metadata configuration has already completed, exiting")
        quit()
    
    # Add gateway rule to allow access to the metadata endpoint
    opnsense.set_gateway_options()
    time.sleep(1)

    # Test if we can reach the metadata endpoint
    if meta.check_metadata() != 200:
        print('Unable to reach metadata endpoint')
        quit()
    
    # Retrieve the hostname
    hostname = meta.get_hostname()
    print (f"Hostname: {hostname}")

    # Retrieve the SSH public key
    public_key = meta.get_public_key()
    print (f"Public key: {public_key}")
    
    password_bcrypt, password_enc = creds.generate_password(public_key)

    # Post password to our metadata endpoint

    meta.post_password(password_enc)
    public_key_b64 = base64.b64encode(public_key)
   
    opnsense.set_system_configuration(
        path = "./config.xml",
        password = password_bcrypt.decode('utf-8'),
        ssh_keys = public_key_b64
    )

    # Write a blank metadata file to specify script does not need to be re-run
    open('./metadata.txt', 'w')
    