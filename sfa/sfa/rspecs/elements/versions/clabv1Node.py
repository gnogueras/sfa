'''
Created on Jun 3, 2014

@author: gerard
'''
from sfa.util.xrn import Xrn, get_leaf
from sfa.util.xml import XpathFilter

from sfa.rspecs.elements.node import NodeElement
from sfa.rspecs.elements.sliver import Sliver
from sfa.rspecs.elements.location import Location
from sfa.rspecs.elements.hardware_type import HardwareType
from sfa.rspecs.elements.disk_image import DiskImage
from sfa.rspecs.elements.interface import Interface
from sfa.rspecs.elements.bwlimit import BWlimit
from sfa.rspecs.elements.pltag import PLTag
from sfa.rspecs.elements.versions.pgv2Services import PGv2Services     
from sfa.rspecs.elements.versions.pgv2SliverType import PGv2SliverType     
from sfa.rspecs.elements.versions.pgv2Interface import PGv2Interface     
from sfa.rspecs.elements.versions.sfav1PLTag import SFAv1PLTag
from sfa.rspecs.elements.granularity import Granularity
from sfa.rspecs.elements.attribute import Attribute

from sfa.rspecs.elements.versions.clabv1Sliver import Clabv1Sliver
from sfa.rspecs.elements.versions.clabv1Interface import Clabv1Interface

class Clabv1Node:
    
    @staticmethod
    def add_nodes(xml, nodes, rspec_content_type=None):
        node_elems = []
        for node in nodes:
            node_fields = ['component_manager_id', 'component_id', 'client_id', 'sliver_id', 'exclusive']
            node_elem = xml.add_instance('node', node, node_fields)
            node_elems.append(node_elem)
            # set component name
            if node.get('component_id'):
                component_name = Xrn.unescape(get_leaf(Xrn(node['component_id']).get_hrn()))
                node_elem.set('component_name', component_name)
            # set hardware types
            if node.get('hardware_types'):
                for hardware_type in node.get('hardware_types', []): 
                    node_elem.add_instance('hardware_type', hardware_type, HardwareType.fields)
            # set location
            if node.get('location'):
                node_elem.add_instance('location', node['location'], Location.fields)       

            # set granularity
            if node.get('exclusive') == "true":
                granularity = node.get('granularity')
                node_elem.add_instance('granularity', granularity, granularity.fields)
            # set interfaces
            Clabv1Interface.add_interfaces(node_elem, node.get('nodeInterfaces'))

            # set available element
            if node.get('available'):
                available_elem = node_elem.add_element('available', now=node['available'])
            # add services
            PGv2Services.add_services(node_elem, node.get('services', [])) 
            # add slivers
            slivers = node.get('slivers', [])
            if not slivers:
                # we must still advertise the available sliver types
                if node.get('sliver_type'):
                    sliver_elem = xml.add_element('sliver_type')
                    sliver_elem.set('name', node['sliver_type'])
            else:
                # Add the slivers of the node
                Clabv1Sliver.add_slivers(node_elem, slivers)

            
            # EXTENSION for C-Lab v1 RSpec Nodes
            # Add group
            group = node.get('group')
            if group:
                group_elem = node_elem.add_element('{%s}group'%xml.namespaces['clab'], name=group['name'], id=group['id'])
            
            # Add Node Network Interfaces
            #node_ifaces = node.get('nodeInterfaces')
            #if node_ifaces:
            #    node_ifaces_elem = node_elem.add_element('node_interfaces')
            #    for node_iface in node_ifaces:
            #        node_ifaces_elem.add_element('node_interface', name=node_iface['name'], type=node_iface['type'])
           
            # Add Management Network Information
            mgmt_net = node.get('mgmt_net')
            if mgmt_net:
                mgmt_net_elem = node_elem.add_element('{%s}management_network'%xml.namespaces['clab'], addr=mgmt_net['addr'])

        return node_elems


    @staticmethod
    def get_nodes(xml, filter={}):
        xpath = '//node%s | //default:node%s' % (XpathFilter.xpath(filter), XpathFilter.xpath(filter))
        node_elems = xml.xpath(xpath)
        return Clabv1Node.get_node_objs(node_elems)

    @staticmethod
    def get_nodes_with_slivers(xml, filter={}):
        xpath = '//node[count(sliver_type)>0] | //default:node[count(default:sliver_type) > 0]' 
        node_elems = xml.xpath(xpath)        
        return Clabv1Node.get_node_objs(node_elems)

    @staticmethod
    def get_node_objs(node_elems):
        nodes = []
        for node_elem in node_elems:
            node = NodeElement(node_elem.attrib, node_elem)
            nodes.append(node) 
            if 'component_id' in node_elem.attrib:
                node['authority_id'] = Xrn(node_elem.attrib['component_id']).get_authority_urn()
            
            # get hardware types
            hardware_type_elems = node_elem.xpath('./default:hardware_type | ./hardware_type')
            node['hardware_types'] = [dict(hw_type.get_instance(HardwareType)) for hw_type in hardware_type_elems]
            
            # get location
            location_elems = node_elem.xpath('./default:location | ./location')
            locations = [dict(location_elem.get_instance(Location)) for location_elem in location_elems]
            if len(locations) > 0:
                node['location'] = locations[0]

            # get granularity
            granularity_elems = node_elem.xpath('./default:granularity | ./granularity')
            if len(granularity_elems) > 0:
                node['granularity'] = granularity_elems[0].get_instance(Granularity)

            # get interfaces
            iface_elems = node_elem.xpath('./default:interface | ./interface')
            node['interfaces'] = [dict(iface_elem.get_instance(Interface)) for iface_elem in iface_elems]

            # get services
            node['services'] = PGv2Services.get_services(node_elem)
            
            # get slivers
            node['slivers'] = Clabv1Sliver.get_slivers(node_elem)    
            
            # get boot state
            available_elems = node_elem.xpath('./default:available | ./available')
            if len(available_elems) > 0 and 'now' in available_elems[0].attrib:
                if available_elems[0].attrib.get('now', '').lower() == 'true': 
                    node['boot_state'] = 'boot'
                else: 
                    node['boot_state'] = 'disabled' 

           # EXTENSION FOR CLab v1 RSpec
           # template
           # overlay
           # sliver interfaces

           
  
        return nodes


    @staticmethod
    def add_slivers(xml, slivers):
        component_ids = []
        for sliver in slivers:
            filter = {}
            if isinstance(sliver, str):
                filter['component_id'] = '*%s*' % sliver
                sliver = {}
            elif 'component_id' in sliver and sliver['component_id']:
                filter['component_id'] = '*%s*' % sliver['component_id']
            if not filter: 
                continue
            nodes = Clabv1Node.get_nodes(xml, filter)
            if not nodes:
                continue
            node = nodes[0]
            Clabv1Sliver.add_slivers(node, sliver)

    @staticmethod
    def remove_slivers(xml, hostnames):
        for hostname in hostnames:
            nodes = Clabv1Node.get_nodes(xml, {'component_id': '*%s*' % hostname})
            for node in nodes:
                slivers = Clabv1Sliver.get_slivers(node.element)
                for sliver in slivers:
                    node.element.remove(sliver.element) 
    