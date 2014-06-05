'''
Created on Jun 4, 2014

@author: gerard
'''

class Clabv1Interface:

    @staticmethod
    def add_interfaces(xml, interfaces):
        if isinstance(interfaces, list):
            for interface in interfaces:
                if_elem = xml.add_instance('{%s}network_interface'%xml.namespaces['clab'], interface, ['name', 'type', 'nr'])
    
    @staticmethod
    def get_interfaces(xml):
        pass
