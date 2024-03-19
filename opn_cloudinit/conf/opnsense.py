import xml.etree.ElementTree as ET
from datetime import datetime
import os
import shutil
from uuid import uuid4

"""

NOTES:
THIS SCRIPT REQUIRES SYSTEM TO HAVE BEEN BUILT ON AT LEAST OPNSENSE 24.1 OR GATEWAY CONFIGURATION WILL FAIL

"""


#### CONSTANTS ####
CONST_OPNSENSE_CONFIG_PATH = '/conf/config.xml'
CONST_OPNSENSE_VAR_GLOBAL_ENABLED = 'enabled'
CONST_OPNSENSE_VAR_GLOBAL_DISABLED = 'enabled'
CONST_OPNSENSE_VAR_SYSTEM_SSH = 'ssh'
CONST_OPNSENSE_VAR_SYSTEM_USER = 'root'

class opnsense:

    def __init__(self):
        print("Opnsense config")

    def backup_config(self, path, action):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f'{path}.{timestamp}.{action}.bak'
        shutil.copyfile(path, backup)
        return backup

    def write_configuration(self, xml, path, backup, action):
        try:
            xml.write(path)
        except Exception as e:
            print(f'Failed write configuration with Exception {e} with executing {action}')
            shutil.copyfile(backup, path)

    def set_system_configuration(self, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        """
        Set System Parameters for opnSense via editing configuration xml

        :param str path: path to config.xml, assumed to be in default location
        :param str hostname: set system hostname
        :param str domain: set system domain
        :param str dnssearchdomain: set dns search
        :param str password: Password Hash for root user in php_bcrypt format https://www.php.net/manual/en/password.constants.php#constant.password-bcrypt
        :param bool ssh: sets SSH status
        :param list dnsservers: list of dns servers
        :param str timezone: timezone in php timezone format
        :param list timeservers: list of ntp servers
        :param bool disablechecksumoffloading: Hardware CRC - Disable hardware checksum offload if True
        :param bool disablechecksumoffloading: Hardware TSO - Disable hardware TCP segmentation offload if True
        :param bool disablechecksumoffloading: Hardware LRO - Disable hardware large receive offload if True
        :param str ssh_keys: base64 encoded string of ssh authorized public keys
        """
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_system')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        system_xml = xml_root.find('system')

        for kwarg in kwargs.keys():
            element = system_xml.find(kwarg)

            #STATIC KEYS
            if('password' == kwarg):
                password_hash = kwargs['password']
                if(len(password_hash) != 60 or password_hash[:2] != "$2"): raise ValueError("Hash Prevalidation Failure, password not in php_bcrypt expected format as per https://www.php.net/manual/en/password.constants.php#constant.password-bcrypt")
                for user in system_xml.findall('user'):
                    if('root' == user.find('name').text): user.find('password').text = password_hash
                continue
            if('ssh_keys' == kwarg):
                for user in system_xml.findall('user'):
                    if('root' == user.find('name').text): #user.find('password').text = password_hash
                        authkeys = user.find('authorizedkeys')
                        if(authkeys is None): authkeys = ET.SubElement(user, 'authorizedkeys')
                        authkeys.text = kwargs['ssh_keys']
                continue
            if(CONST_OPNSENSE_VAR_SYSTEM_SSH == kwarg):
                status_element = element.find(CONST_OPNSENSE_VAR_GLOBAL_ENABLED)
                if(status_element is None): status_element = ET.SubElement(element, CONST_OPNSENSE_VAR_GLOBAL_ENABLED)
                if(kwargs[kwarg]): status_element.text = CONST_OPNSENSE_VAR_GLOBAL_ENABLED
                else: status_element.text = CONST_OPNSENSE_VAR_GLOBAL_DISABLED
                continue
            if('dnsservers' == kwarg):
                for dnsserver in system_xml.findall("dnsserver"):
                    if(dnsserver.text not in kwargs['dnsservers']): system_xml.remove(dnsserver)
                    else: kwargs['dnsservers'].remove(dnsserver.text)
                for new_server in kwargs['dnsservers']:
                    new_dns = ET.SubElement(system_xml, 'dnsserver')
                    new_dns.text = new_server
                continue
            if('timeservers' == kwarg):
                system_xml.find(kwarg).text = " ".join(kwargs[kwarg])
                continue
            
            # DYNAMIC KEYS
            if(element is None): 
                print(f'WARNING!!! option {kwarg} does not exist, creating {kwarg}, if this is unintend, please rollback configuation')
                element = ET.SubElement(system_xml, kwarg)
            system_xml.find(kwarg).text = str(kwargs[kwarg])
        self.write_configuration(xml_tree, path, backup, 'set_system')
        return True

    def set_system_tunable(self, tunable, path=CONST_OPNSENSE_CONFIG_PATH, value='default', description=None):
        """
        Set System Tunable for opnSense via editing configuration xml

        :param str path: path to config.xml, assumed to be in default location
        :param str tunable: tunable item you want to set, if not found, will be created
        :param str value: value of tunable
        :param str description: set description if set
        """
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_tunable')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        sysctl_xml = xml_root.find('sysctl')

        found = False
        for tunable_item in sysctl_xml.findall('item'):
            if(tunable_item.find("tunable").text == tunable):
                found = True
                tunable_item.find("value").text = value
                if(description): tunable_item.find("descr").text = description
        if(not found):
            new_tunable = ET.SubElement(sysctl_xml, 'item')
            ET.SubElement(new_tunable, 'tunable').text = tunable
            ET.SubElement(new_tunable, 'value').text = value
            if(description): 
                ET.SubElement(new_tunable, 'descr').text = description
        self.write_configuration(xml_tree, path, backup, 'set_tunable')
        return True

    def set_interface(self, interface, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        """
        Set System Tunable for opnSense via editing configuration xml

        :param str interface: which network interface to set
        :param str path: path to config.xml, assumed to be in default location
        :param str keywords: set keyword configuation value.
        :param str ipaddr: set IP address for interface, can also be set to dhcp
        """
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_interface')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        interfaces_xml = xml_root.find('interfaces')

        if('iface' in kwargs):
            kwargs['if'] = kwargs['iface']
            del kwargs['iface']

        iface = interfaces_xml.find(interface)
        if(iface):
            for kwarg in kwargs.keys():
                element = iface.find(kwarg)
                if(element is not None): element.text = str(kwargs[kwarg])
                if(element is None): ET.SubElement(iface, kwarg).text = str(kwargs[kwarg])
        else:
            iface = ET.SubElement(interfaces_xml, interface)
            for kwarg in kwargs.keys():
                ET.SubElement(iface, kwarg).text = str(kwargs[kwarg])
        ipaddr = iface.find("ipaddr")
        if(ipaddr is not None):
            if(ipaddr.text == 'dhcp'):
                subnet = iface.find('subnet')
                if(subnet is not None): iface.remove(subnet)

        xml_tree.write(path)
        return True

    def set_dhcpd_options(self, interface, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        """
        Set System Tunable for opnSense via editing configuration xml

        :param str interface: which network interface with dhcpd options set
        :param str path: path to config.xml, assumed to be in default location
        :param str keywords: set keyword configuation value.
        """
        
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_dhcpd')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        dhcpd_interfaces_xml = xml_root.find('dhcpd')

        

        iface = dhcpd_interfaces_xml.find(interface)
        if(iface is None):
            iface = ET.SubElement(dhcpd_interfaces_xml, interface)
        
        for kwarg in kwargs.keys():
            element = iface.find(kwarg)
            if('range' == kwarg):
                continue
            if(element is not None): element.text = str(kwargs[kwarg])
            if(element is None): ET.SubElement(iface, kwarg).text = str(kwargs[kwarg])
        
        self.write_configuration(xml_tree, path, backup, 'set_dhcpd')
        return True

    def set_gateway_options(self, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_gateway_options')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        opnsense_xml = xml_root.find('OPNsense')
        gateways_xml = opnsense_xml.find('Gateways')

        gw_item = None

        for gateway_item in gateways_xml.findall('gateway_item'):
            if(gateway_item.find('gateway').text == kwargs['gateway']): gw_item = gateway_item
        if(gw_item is None):
            gw_item = ET.SubElement(gateways_xml, 'gateway_item')
            gw_item.set('uuid', str(uuid4()))
            ET.SubElement(gw_item, 'disabled').text = str(1)
            ET.SubElement(gw_item, 'name').text = 'Generated by CloudInit for OpnSense'
            ET.SubElement(gw_item, 'descr').text = 'Generated by CloudInit for OpnSense'
            ET.SubElement(gw_item, 'interface').text = 'wan'
            ET.SubElement(gw_item, 'ipprotocol').text = 'inet'
            ET.SubElement(gw_item, 'gateway').text = '169.254.1.1'
            ET.SubElement(gw_item, 'fargw').text = str(0)
            ET.SubElement(gw_item, 'monitor_disable').text = str(1)
            ET.SubElement(gw_item, 'monitor_noroute').text = str(0)
            ET.SubElement(gw_item, 'monitor')
            ET.SubElement(gw_item, 'force_down').text = str(0)
            ET.SubElement(gw_item, 'priority').text = str(255)
            ET.SubElement(gw_item, 'weight').text = str(255)
            ET.SubElement(gw_item, 'latencylow')
            ET.SubElement(gw_item, 'latencyhigh')
            ET.SubElement(gw_item, 'latencylow')
            ET.SubElement(gw_item, 'losshigh')
            ET.SubElement(gw_item, 'interval')
            ET.SubElement(gw_item, 'time_period')
            ET.SubElement(gw_item, 'loss_interval')
            ET.SubElement(gw_item, 'data_length')
        
        for kwarg in kwargs.keys():
            try:
                gw_item.find(kwarg).text = str(kwargs[kwarg])
            except:
                raise ValueError(f'Option {kwarg} does not exist as a gateway option')

        self.write_configuration(xml_tree, path, backup, 'set_gateway_option')
        return True

    def set_gateway_route(self, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_configbackup_config(path, 'create_filter_rule')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        routes_xml = xml_root.find('staticroutes')

        route = None

        for route_item in routes_xml.findall('route'):
            if(route_item.find('network').text == kwargs['network']): route = route_item
        if(route is None):
            route = ET.SubElement(routes_xml, 'route')
            route.set('uuid', str(uuid4()))
            ET.SubElement(route, 'disabled').text = str(1)
            ET.SubElement(route, 'network')
            ET.SubElement(route, 'descr').text = 'Generated by CloudInit for OpnSense'
            ET.SubElement(route, 'gateway')
        
        for kwarg in kwargs.keys():
            try:
                route.find(kwarg).text = str(kwargs[kwarg])
            except:
                raise ValueError(f'Option {kwarg} does not exist as a gateway option')

        self.write_configuration(xml_tree, path, backup, 'set_route')
        return True

    def create_firewall_filter_role(self, path=CONST_OPNSENSE_CONFIG_PATH, **kwargs):
        if(not os.path.isfile(path)): raise ValueError(f"Config File {path} does not exist")
        backup = self.backup_config(path, 'set_gateway_options')
        xml_tree = ET.parse(path)
        xml_root = xml_tree.getroot()
        filter_xml = xml_root.find('filter')

        rule = ET.SubElement(filter_xml, 'rule')

        rule.set('uuid', str(uuid4()))
        ET.SubElement(rule, 'type').text = 'pass'
        ET.SubElement(rule, 'ipprotocol').text = 'inet'
        ET.SubElement(rule, 'interface').text = 'lan'
        ET.SubElement(rule, 'interface').text = 'lan'
        src = ET.SubElement(rule, 'source')
        dst = ET.SubElement(rule, 'destination')

        created = ET.SubElement(rule, 'created')
        ET.SubElement(created, 'username').text = 'root@127.0.0.1'
        ET.SubElement(created, 'time').text = str(datetime.now().timestamp())
        ET.SubElement(created, 'description').text = 'cloudinit.py ZeroOneTech init'

        if('source' in kwargs):
            kwarg = 'source'
            if('any' == kwargs[kwarg]): ET.SubElement(src, 'any')
            elif(kwargs[kwarg].split(':')[0] == 'addr'): ET.SubElement(src, 'address').text = kwargs[kwarg].split(':')[1]
            elif(kwargs[kwarg].split(':')[0] == 'net'): ET.SubElement(src, 'network').text = kwargs[kwarg].split(':')[1]
            del kwargs[kwarg]
        if('destination' in kwargs):
            kwarg = 'destination'
            if('any' == kwargs[kwarg]): ET.SubElement(dst, 'any')
            elif(kwargs[kwarg].split(':')[0] == 'addr'): ET.SubElement(dst, 'address').text = kwargs[kwarg].split(':')[1]
            elif(kwargs[kwarg].split(':')[0] == 'net'): ET.SubElement(dst, 'network').text = kwargs[kwarg].split(':')[1]
            del kwargs[kwarg]
        
        for kwarg in kwargs.keys():
            if('source' == kwarg):
                if('any' == kwargs[kwarg]): ET.SubElement(src, 'any')
                elif(kwargs[kwarg].split(':')[0] == 'addr'): ET.SubElement(src, 'address').text = kwargs[kwarg].split(':')[1]
                elif(kwargs[kwarg].split(':')[0] == 'net'): ET.SubElement(src, 'network').text = kwargs[kwarg].split(':')[1]
                del kwargs[kwarg]
                continue
            if('destination' == kwarg):
                if('any' == kwargs[kwarg]): ET.SubElement(dst, 'any')
                elif(kwargs[kwarg].split(':')[0] == 'addr'): ET.SubElement(dst, 'address').text = kwargs[kwarg].split(':')[1]
                elif(kwargs[kwarg].split(':')[0] == 'net'): ET.SubElement(dst, 'network').text = kwargs[kwarg].split(':')[1]
                del kwargs[kwarg]
                continue
            element = rule.find(kwarg)
            if(element is None): element = ET.SubElement(rule, kwarg)
            element.text = str(kwargs[kwarg])
            
        updated = ET.SubElement(rule, 'created')
        ET.SubElement(updated, 'username').text = 'root@127.0.0.1'
        ET.SubElement(updated, 'time').text = str(datetime.now().timestamp())
        ET.SubElement(updated, 'description').text = 'cloudinit.py ZeroOneTech init'

        self.write_configuration(xml_tree, path, backup, 'create_filter_rule')
        return True

#set_system_configuration(hostname='fathackers-badcode',
#                         domain='yolocolo.zeroone.tech',
#                         dnssearchdomain='yolocolo.zeroone.tech',
#                         path="config.xml", 
#                         password=password_hash('opnsense'),
#                         ssh=True,
#                         dnsservers=['1.1.1.1','1.0.0.1'],
#                         timezone='Etc/UTC',
#                         timeservers=['0.au.pool.ntp.org','1.au.pool.ntp.org','2.au.pool.ntp.org'],
#                         disablechecksumoffloading=1,
#                         disablesegmentationoffloading=1,
#                         disablelargereceiveoffloading=0,
#                         ssh_keys='c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFDd3JsVXFBeXdNYlU3VWI4ZGVaV21wdEVSRi9CaWJOU2RHS0taOC9aME1naUp4R3oyejhwb1psQUdmVjlMajhmMjFadkJpRE9LV21wS1pCK0pwZG0vQUJKNnBGWHdSL0FPOEtyWXVjanBWb29kVnA4M3FCZGpHSWtXZEsydS9EQUdTdWVyakNCV3hOV0pFdU9jUDhBRmhUTHVhWG1FT0g2T1dTTHJYN25xV0h4cGZBbklabzB3V204Vm03d2ZqSnRzckE4VFNZQis4aDN3cXdIeHltdnpyZ0diVm9od01PRFlwcThjblZaenNmK1BJZ05ld1hiUmYxTHUrcFRKZ1l6bWtNa1NFM09rbVR4ZGFjakd4SlFRaEYrcXhTSGFhR3BKZnpsZGF3bVc0L0FrMUlzbjJsdnlXL2ZDbXFtZk5iMEtob0p1NkV5dEdFdDMwMnhWUDVSamQgcnNhLWtleS0yMDI0MDIyNg')
#set_system_tunable("test", path='config.xml', value='test', description='testing')
#set_interface("lan", path='config.xml', ipaddr='dhcp')
#set_dhcpd_options("lan", path='config.xml', enabled=0)
#
#CONST_METADATA_GW_NAME = 'GW_METADATA_API'
#set_gateway_options(path="config.xml", gateway='172.16.0.11', descr='OpenStack Metadata API', disabled=0, interface='lan', name=CONST_METADATA_GW_NAME)
#set_gateway_route(path="config.xml", network='169.254.169.254/32', gateway=CONST_METADATA_GW_NAME, disabled=1)
#set_gateway_route(path="config.xml", network='169.254.169.253/32', gateway=CONST_METADATA_GW_NAME, disabled=0)


#create_firewall_filter_role(path="config.xml", 
#                            type='pass', 
#                            interface='lan',
#                            ipprotocol='inet',
#                            statetype='keep state',
#                            gateway=CONST_METADATA_GW_NAME,
#                            direction='in',
#                            quick=1,
#                            source='net:lanip',
#                            destination='addr:169.254.169.254',
#                            descr='OpenStack Metadata API Access'
#                        )
#create_firewall_filter_role(path="config.xml", 
#                            type='pass', 
#                            interface='lan',
#                            ipprotocol='inet',
#                            statetype='keep state',
#                            gateway=CONST_METADATA_GW_NAME,
#                            direction='out',
#                            quick=1,
#                            source='addr:169.254.169.254',
#                            destination='any',
#                            descr='OpenStack Metadata API Access'
#                        )