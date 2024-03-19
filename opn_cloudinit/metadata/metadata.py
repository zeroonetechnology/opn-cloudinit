import requests
import string

METADATA_ENDPOINT_ROOT = 'http://169.254.169.254'
METADATA_HOSTNAME = '/latest/meta-data/hostname'
METADATA_PUBLIC_KEY = '/latest/meta-data/public-keys/0/openssh-key'
METADATA_PASSWORD = '/openstack/2013-04-04/password'

class metadata:

    def __init__(self):
        pass

    def check_metadata() -> int:
        try:
            r = requests.get(METADATA_ENDPOINT_ROOT)
            r.raise_for_status()
            print (f"Return code: {r.status_code}")
            return r.status_code
        except requests.exceptions.RequestException as e:
            raise e

    def get_hostname(self) -> str:
        type = 'hostname'
        hostname = self.retrieve_metadata_value(type)
        return hostname
    
    def get_public_key(self) -> str:
        type = 'public_key'
        public_key = self.retrieve_metadata_value(type)
        return public_key
    
    def put_password(self, password: str) -> bool:
        pass

    def retrieve_metadata_value(type: str, root: str=METADATA_ENDPOINT_ROOT) -> str:
        match type:
            case 'hostname':
                url = root + METADATA_HOSTNAME
            case 'public_key':
                url = root + METADATA_PUBLIC_KEY
        try:
            r = requests.get(url)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:
            raise e
        
    def post_metadata_value(self, type: str, value: str, root: str=METADATA_ENDPOINT_ROOT) -> bool:
        match type:
            case 'password':
                url = root + METADATA_PASSWORD
        try:
            r = requests.post(url, value)
            r.raise_for_status()
            return True
        except requests.exceptions.HTTPError as http_error:
            if http_error.response.status_code == 409:
                print("Password has already been posted")
            return True
        except requests.exceptions.RequestException as e:
            raise e