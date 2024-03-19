import requests

METADATA_ENDPOINT_ROOT = 'http://169.254.169.254'
METADATA_HOSTNAME = '/latest/meta-data/hostname'
METADATA_PUBLIC_KEY = '/latest/meta-data/public-keys/0/openssh-key'
METADATA_PASSWORD = '/openstack/2013-04-04/password'


class metadata:
    def check_metadata():
        r = requests.get(METADATA_ENDPOINT_ROOT)
        if r.status_code != '200':
            quit
        print (f"Return code: {r.status_code}")

    def retrieve_metadata():
        pass

    def post_metadata():
        pass