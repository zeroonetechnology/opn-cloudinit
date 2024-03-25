'''
TESTING OF FUNCTIONS WITH OPENSTACK API

All Values used in this script are used for testing purposes only!

'''

from opn_cloudinit.conf.opnsense import opnsense as opnsense_conf
from opn_cloudinit.metadata.metadata import metadata as metadata
from opn_cloudinit.creds.credentials import credentials as credentials

opnsense = opnsense_conf()
meta = metadata()
creds = credentials()

'''
Set System Values for System
'''
opnsense.set_system_configuration(hostname='fathackers-badcode',
                         domain='yolocolo.zeroone.tech',
                         dnssearchdomain='yolocolo.zeroone.tech',
                         path="config.xml", 
                         password="$2y$11$e7uhWO2UauHIwDiVHNG8dutm58RoRn4tRqsmJKRAAfPLgrgwwEFUO", # Bcrypt Hash of "Hello, World!"
                         ssh=True,
                         dnsservers=['1.1.1.1','1.0.0.1'],
                         timezone='Etc/UTC',
                         timeservers=['0.au.pool.ntp.org','1.au.pool.ntp.org','2.au.pool.ntp.org'],
                         disablechecksumoffloading=1,
                         disablesegmentationoffloading=1,
                         disablelargereceiveoffloading=0,
                         ssh_keys='c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFDd3JsVXFBeXdNYlU3VWI4ZGVaV21wdEVSRi9CaWJOU2RHS0taOC9aME1naUp4R3oyejhwb1psQUdmVjlMajhmMjFadkJpRE9LV21wS1pCK0pwZG0vQUJKNnBGWHdSL0FPOEtyWXVjanBWb29kVnA4M3FCZGpHSWtXZEsydS9EQUdTdWVyakNCV3hOV0pFdU9jUDhBRmhUTHVhWG1FT0g2T1dTTHJYN25xV0h4cGZBbklabzB3V204Vm03d2ZqSnRzckE4VFNZQis4aDN3cXdIeHltdnpyZ0diVm9od01PRFlwcThjblZaenNmK1BJZ05ld1hiUmYxTHUrcFRKZ1l6bWtNa1NFM09rbVR4ZGFjakd4SlFRaEYrcXhTSGFhR3BKZnpsZGF3bVc0L0FrMUlzbjJsdnlXL2ZDbXFtZk5iMEtob0p1NkV5dEdFdDMwMnhWUDVSamQgcnNhLWtleS0yMDI0MDIyNg')
'''
Sets Any System Tunables
'''
opnsense.set_system_tunable("test", path='config.xml', value='test', description='testing')
'''
Sets Interface Options
'''
opnsense.set_interface("lan", path='config.xml', ipaddr='dhcp')
'''
Sets DHCPD Options
'''
opnsense.set_dhcpd_options("lan", path='config.xml', enabled=0)


'''
Configures Gateway options and routes to enable Metadata API Access over LAN interface
'''
CONST_METADATA_GW_NAME = 'GW_METADATA_API'
opnsense.set_gateway_options(path="config.xml", gateway='172.16.0.11', descr='OpenStack Metadata API', disabled=0, interface='lan', name=CONST_METADATA_GW_NAME)
opnsense.set_gateway_route(path="config.xml", network='169.254.169.254/32', gateway=CONST_METADATA_GW_NAME, disabled=1)
opnsense.set_gateway_route(path="config.xml", network='169.254.169.253/32', gateway=CONST_METADATA_GW_NAME, disabled=0)
opnsense.create_firewall_filter_role(path="config.xml", 
                            type='pass', 
                            interface='lan',
                            ipprotocol='inet',
                            statetype='keep state',
                            gateway=CONST_METADATA_GW_NAME,
                            direction='in',
                            quick=1,
                            source='net:lanip',
                            destination='addr:169.254.169.254',
                            descr='OpenStack Metadata API Access'
                        )
opnsense.create_firewall_filter_role(path="config.xml", 
                            type='pass', 
                            interface='lan',
                            ipprotocol='inet',
                            statetype='keep state',
                            gateway=CONST_METADATA_GW_NAME,
                            direction='out',
                            quick=1,
                            source='addr:169.254.169.254',
                            destination='any',
                            descr='OpenStack Metadata API Access'
                        )
'''
Configures Config Access from WAN Interface
'''
CONST_NAT_RULE_ID = "nat_configoverwan.cloudinit" # NOTE FORMAT FROM OPNSENSE is nat_66011e9e1e2d94.57573960 but review appears to be exact match, not some other meaning but review is required
opnsense.create_firewall_filter_role(path="config.xml", 
                            associated_rule_id=CONST_NAT_RULE_ID, 
                            interface='wan',
                            ipprotocol='inet',
                            protocol='tcp',
                            statetype='keep state',
                            source='any', # Intending to use OpenStack SG's for ACL, but can also use addr:192.0.0.0
                            destination='addr:127.0.0.1:443',
                            descr='ALLOW WEBCONSOLE ACCESS OVER WAN!!!'
                        )
opnsense.create_firewall_nat_role(path="config.xml", 
                            associated_rule_id=CONST_NAT_RULE_ID,
                            protocol='tcp',
                            interface='wan',
                            ipprotocol='inet',
                            descr='ALLOW WEBCONSOLE ACCESS OVER WAN!!!',
                            target='127.0.0.1',
                            local_port='443',
                            destination='net:wanip:443',
                            source='any'
                        )
