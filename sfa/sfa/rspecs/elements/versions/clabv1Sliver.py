'''
Created on Jun 3, 2014

@author: gerard
'''
from sfa.rspecs.elements.element import Element
from sfa.rspecs.elements.sliver import Sliver
from sfa.rspecs.elements.versions.pgv2DiskImage import PGv2DiskImage
from sfa.rspecs.elements.versions.plosv1FWRule import PLOSv1FWRule

from sfa.rspecs.elements.versions.clabv1SliverParameters import Clabv1SliverParameters
from sfa.rspecs.elements.versions.clabv1SliverParameters import Clabv1Template
from sfa.rspecs.elements.versions.clabv1SliverParameters import Clabv1Overlay
from sfa.rspecs.elements.versions.clabv1SliverParameters import Clabv1NetworkInterface


#from sfa.rspecs.elements.versions.pgv2SliverType import PGv2SliverType

class Clabv1Sliver:

    @staticmethod
    def add_slivers(xml, slivers):
        if not slivers:
            return 
        if not isinstance(slivers, list):
            slivers = [slivers]
            
        for sliver in slivers: 
            sliver_elem = xml.add_element('sliver_type')
            if sliver.get('type'):
                sliver_elem.set('name', sliver['type'])
            attrs = ['client_id', 'cpus', 'memory', 'storage']
            for attr in attrs:
                if sliver.get(attr):
                    sliver_elem.set(attr, sliver[attr])
            
            images = sliver.get('disk_image')
            if images and isinstance(images, list):
                PGv2DiskImage.add_images(sliver_elem, images)      
            fw_rules = sliver.get('fw_rules')
            if fw_rules and isinstance(fw_rules, list):
                PLOSv1FWRule.add_rules(sliver_elem, fw_rules)
            Clabv1Sliver.add_sliver_attributes(sliver_elem, sliver.get('tags', []))
            
            # EXTENSION FOR CLab v1 RSpec
            sliver_parameters_elem = xml.add_element('{%s}sliver_parameters'%xml.namespaces['clab'])
            # template
            template = sliver.get('template')
            if template:
                sliver_parameters_elem.add_element('{%s}template'%xml.namespaces['clab'], name=template['name'], id=str(template['id']), type=template['type'])
            # overlay
            overlay = sliver.get('overlay')
            if overlay:
                sliver_parameters_elem.add_element('{%s}overlay'%xml.namespaces['clab'], name=overlay['uri'], uri=overlay['uri'])
            # interfaces
            #sliver_interfaces_elem = sliver_parameters_elem.add_element('{%s}sliver_interfaces'%xml.namespaces['clab'])
            interfaces = sliver.get('interfaces')
            if interfaces:
                for interface in interfaces:
                    sliver_parameters_elem.add_element('{%s}network_interface'%xml.namespaces['clab'], name=interface['name'], nr=str(interface['nr']), type=interface['type'])
                    #sliver_interfaces_elem.add_element('{%s}network_interface'%xml.namespaces['clab'], name=interface['name'], nr=str(interface['nr']), type=interface['type'])
            
    
    @staticmethod
    def add_sliver_attributes(xml, attributes):
        if attributes: 
            for attribute in attributes:
                if attribute['name'] == 'initscript':
                    xml.add_element('{%s}initscript' % xml.namespaces['planetlab'], name=attribute['value'])
                elif attribute['tagname'] == 'flack_info':
                    attrib_elem = xml.add_element('{%s}info' % xml.namespaces['flack'])
                    attrib_dict = None #eval(tag['value'])
                    for (key, value) in attrib_dict.items():
                        attrib_elem.set(key, value)                
    @staticmethod
    def get_slivers(xml, filter={}):
        xpath = './default:sliver_type | ./sliver_type'
        sliver_elems = xml.xpath(xpath)
        slivers = []
        
        for sliver_elem in sliver_elems:
            sliver = Sliver(sliver_elem.attrib,sliver_elem)
            
            if 'component_id' in xml.attrib:     
                sliver['component_id'] = xml.attrib['component_id']
            if 'name' in sliver_elem.attrib:
                sliver['type'] = sliver_elem.attrib['name']
            sliver['disk_image'] = PGv2DiskImage.get_images(sliver_elem)
            sliver['fw_rules'] = PLOSv1FWRule.get_rules(sliver_elem)
            
            # EXTENSION FOR CLab v1 RSpec
            from sfa.util.sfalogging import logger
            try:
                # Obtain the Complex element sliver_parameters
                # xpath command returns a list. Use '[0]' to get the single element (only one element in the returned list)
                xpath = './clab:sliver_parameters | ./sliver_parameters'
                sliver_parameters_elem = xml.xpath(xpath, namespaces=xml.namespaces)[0]
                sliver_parameters = Clabv1SliverParameters(sliver_parameters_elem.attrib, sliver_parameters_elem)
           
                # get the template element
                template_elems = sliver_parameters_elem.xpath('./clab:template | ./template', namespaces=xml.namespaces)
                if template_elems:
                    template_elem = template_elems[0]  
                    template = dict(template_elem.get_instance(Clabv1Template))
                    sliver['template'] = template
                # get the overlay element
                overlay_elems = sliver_parameters_elem.xpath('./clab:overlay | ./overlay', namespaces=xml.namespaces)
                if overlay_elems:
                    overlay_elem = overlay_elems[0]  
                    overlay = dict(overlay_elem.get_instance(Clabv1Overlay))
                    sliver['overlay'] = overlay
                # get the sliver interfaces element (list of SliverInterface elems)
                #sliver_interfaces_elems = sliver_parameters_elem.xpath('./clab:sliver_interfaces | ./sliver_interfaces', namespaces=xml.namespaces)
                #if sliver_interfaces_elems:
                #    sliver_interfaces_elem = sliver_interfaces_elems[0]  
                #    sliver_network_iface_elems = sliver_interfaces_elem.xpath('./clab:network_interface | ./network_interface', namespaces=xml.namespaces)
                #    sliver_network_ifaces = [dict(sliver_network_iface_elem.get_instance(Clabv1NetworkInterface)) for sliver_network_iface_elem in sliver_network_iface_elems]
                #    sliver['sliver_interfaces'] = sliver_network_ifaces
                    
                sliver_network_iface_elems = sliver_parameters_elem.xpath('./clab:network_interface | ./network_interface', namespaces=xml.namespaces)
                if sliver_network_iface_elems:
                    sliver_network_ifaces = [dict(sliver_network_iface_elem.get_instance(Clabv1NetworkInterface)) for sliver_network_iface_elem in sliver_network_iface_elems]
                    sliver['sliver_interfaces'] = sliver_network_ifaces
                
            except Exception:
                # there is no element sliver_parameters in the xml
                pass
            slivers.append(sliver)
        return slivers

    @staticmethod
    def get_sliver_attributes(xml, filter={}):
        return []             
