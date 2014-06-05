'''
Created on Jun 3, 2014

@author: gerard
'''
from copy import deepcopy
from StringIO import StringIO
from sfa.util.xrn import Xrn
from sfa.rspecs.version import RSpecVersion

from sfa.rspecs.versions.pgv3 import GENIv3
from sfa.rspecs.elements.versions.clabv1Node import Clabv1Node
from sfa.rspecs.elements.versions.clabv1Sliver import Clabv1Sliver

SCHEMA = "file:///home/gerard/Dropbox/KTH/Thesis/clab.xsd" 
XMLNS = "file:///home/gerard/Dropbox/KTH/Thesis/clab.xsd" 
NAMESPACE = "http://www.geni.net/resources/rspec/3"

# Examples
# schema = 'http://senslab.info/resources/rspec/1/ad.xsd'
# namespace = 'http://www.geni.net/resources/rspec/3'
# XMLNS extensions = { flack': "http://www.protogeni.net/resources/rspec/ext/flack/1" }


class Clabv1(GENIv3):
    type = 'CLab'
    content_type = 'ad'
    version = '1'
    schema = SCHEMA
    namespace = NAMESPACE
    extensions = {
        #'flack': "http://www.protogeni.net/resources/rspec/ext/flack/1",
        #'planetlab': "http://www.planet-lab.org/resources/sfa/ext/planetlab/1",
        #'plos': "http://www.planet-lab.org/resources/sfa/ext/plos/1",
        'clab': XMLNS,
    }
    namespaces = dict(extensions.items() + [('default', namespace)])

  
    # Nodes

    def get_nodes(self, filter=None):
        return Clabv1Node.get_nodes(self.xml, filter)

    def get_nodes_with_slivers(self):
        return Clabv1Node.get_nodes_with_slivers(self.xml)

    def add_nodes(self, nodes, check_for_dupes=False, rspec_content_type=None):
        return Clabv1Node.add_nodes(self.xml, nodes, rspec_content_type)
    
    def merge_node(self, source_node_tag):
        # this is untested
        self.xml.root.append(deepcopy(source_node_tag))

    # Slivers
    
    def get_sliver_attributes(self, hostname, network=None):
        nodes = self.get_nodes({'component_id': '*%s*' %hostname})
        attribs = []
        if nodes is not None and isinstance(nodes, list) and len(nodes) > 0:
            node = nodes[0]
            sliver = node.xpath('./default:sliver_type', namespaces=self.namespaces)
            if sliver is not None and isinstance(sliver, list) and len(sliver) > 0:
                sliver = sliver[0]
                #attribs = self.attributes_list(sliver)
        return attribs

    def get_slice_attributes(self, network=None):
        slice_attributes = []
        nodes_with_slivers = self.get_nodes_with_slivers()
        # TODO: default sliver attributes in the PG rspec?
        default_ns_prefix = self.namespaces['default']
        for node in nodes_with_slivers:
            sliver_attributes = self.get_sliver_attributes(node, network)
            for sliver_attribute in sliver_attributes:
                name=str(sliver_attribute[0])
                text =str(sliver_attribute[1])
                attribs = sliver_attribute[2]
                # we currently only suppor the <initscript> and <flack> attributes
                if  'info' in name:
                    attribute = {'name': 'flack_info', 'value': str(attribs), 'node_id': node}
                    slice_attributes.append(attribute)
                elif 'initscript' in name:
                    if attribs is not None and 'name' in attribs:
                        value = attribs['name']
                    else:
                        value = text
                    attribute = {'name': 'initscript', 'value': value, 'node_id': node}
                    slice_attributes.append(attribute)

        return slice_attributes

    def attributes_list(self, elem):
        opts = []
        if elem is not None:
            for e in elem:
                opts.append((e.tag, str(e.text).strip(), e.attrib))
        return opts

    def get_default_sliver_attributes(self, network=None):
        return []

    def add_default_sliver_attribute(self, name, value, network=None):
        pass

    def add_slivers(self, hostnames, attributes=[], sliver_urn=None, append=False):
        # all nodes hould already be present in the rspec. Remove all
        # nodes that done have slivers
        for hostname in hostnames:
            node_elems = self.get_nodes({'component_id': '*%s*' % hostname})
            if not node_elems:
                continue
            node_elem = node_elems[0]
            
            # determine sliver types for this node
            valid_sliver_types = ['emulab-openvz', 'raw-pc', 'plab-vserver', 'plab-vnode','RD_sliver']
            requested_sliver_type = None
            for sliver_type in node_elem.get('slivers', []):
                if sliver_type.get('type') in valid_sliver_types:
                    requested_sliver_type = sliver_type['type']
            
            if not requested_sliver_type:
                continue
            sliver = {'type': requested_sliver_type,
                     'pl_tags': attributes}

            # remove available element
            for available_elem in node_elem.xpath('./default:available | ./available'):
                node_elem.remove(available_elem)
            
            # remove interface elements
            for interface_elem in node_elem.xpath('./default:interface | ./interface'):
                node_elem.remove(interface_elem)
        
            # remove existing sliver_type elements
            for sliver_type in node_elem.get('slivers', []):
                node_elem.element.remove(sliver_type.element)

            # set the client id
            node_elem.element.set('client_id', hostname)
            if sliver_urn:
                pass
                # TODO
                # set the sliver id
                #slice_id = sliver_info.get('slice_id', -1)
                #node_id = sliver_info.get('node_id', -1)
                #sliver_id = Xrn(xrn=sliver_urn, type='slice', id=str(node_id)).get_urn()
                #node_elem.set('sliver_id', sliver_id)

            # add the sliver type elemnt    
            Clabv1Sliver.add_slivers(node_elem.element, sliver)         

        # remove all nodes without slivers
        if not append:
            for node_elem in self.get_nodes():
                if not node_elem['client_id']:
                    parent = node_elem.element.getparent()
                    parent.remove(node_elem.element)

    def remove_slivers(self, slivers, network=None, no_dupes=False):
        Clabv1Node.remove_slivers(self.xml, slivers) 


# MODIFY THE SCHEMA
# ADD THE EXTENSION OF CLAB

class Clabv1Ad(Clabv1):
    enabled = True
    content_type = 'ad'
    schema = 'http://www.protogeni.net/resources/rspec/2/ad.xsd'
    template = '<rspec type="advertisement" xmlns="http://www.protogeni.net/resources/rspec/2" xmlns:clab="' + XMLNS + '" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.protogeni.net/resources/rspec/2 http://www.protogeni.net/resources/rspec/2/ad.xsd ' + XMLNS + ' ' + SCHEMA + '" />'

class Clabv1Request(Clabv1):
    enabled = True
    content_type = 'request'
    schema = 'http://www.protogeni.net/resources/rspec/2/request.xsd'
    #template = '<rspec type="request" xmlns="http://www.protogeni.net/resources/rspec/2" xmlns:flack="http://www.protogeni.net/resources/rspec/ext/flack/1" xmlns:plos="http://www.planet-lab.org/resources/sfa/ext/plos/1" xmlns:planetlab="http://www.planet-lab.org/resources/sfa/ext/planetlab/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.protogeni.net/resources/rspec/2 http://www.protogeni.net/resources/rspec/2/request.xsd http://www.planet-lab.org/resources/sfa/ext/planetlab/1 http://www.planet-lab.org/resources/sfa/ext/planetlab/1/planetlab.xsd http://www.planet-lab.org/resources/sfa/ext/plos/1 http://www.planet-lab.org/resources/sfa/ext/plos/1/plos.xsd"/>'
    template = '<rspec type="request" xmlns="http://www.protogeni.net/resources/rspec/2" xmlns:clab="' + XMLNS + '" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.protogeni.net/resources/rspec/2 http://www.protogeni.net/resources/rspec/2/ad.xsd ' + XMLNS + ' ' + SCHEMA + '" />'


class Clabv1Manifest(Clabv1):
    enabled = True
    content_type = 'manifest'
    schema = 'http://www.protogeni.net/resources/rspec/2/manifest.xsd'
    #template = '<rspec type="manifest" xmlns="http://www.protogeni.net/resources/rspec/2" xmlns:plos="http://www.planet-lab.org/resources/sfa/ext/plos/1" xmlns:flack="http://www.protogeni.net/resources/rspec/ext/flack/1" xmlns:planetlab="http://www.planet-lab.org/resources/sfa/ext/planetlab/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.protogeni.net/resources/rspec/2 http://www.protogeni.net/resources/rspec/2/manifest.xsd http://www.planet-lab.org/resources/sfa/ext/planetlab/1 http://www.planet-lab.org/resources/sfa/ext/planetlab/1/planetlab.xsd http://www.planet-lab.org/resources/sfa/ext/plos/1 http://www.planet-lab.org/resources/sfa/ext/plos/1/plos.xsd"/>'
    template = '<rspec type="manifest" xmlns="http://www.protogeni.net/resources/rspec/2" xmlns:clab="' + XMLNS + '" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.protogeni.net/resources/rspec/2 http://www.protogeni.net/resources/rspec/2/ad.xsd ' + XMLNS + ' ' + SCHEMA + '" />'

     
#if __name__ == '__main__':
#    from sfa.rspecs.rspec import RSpec
#    from sfa.rspecs.rspec_elements import *
#    r = RSpec('/tmp/clabv1.rspec')
#    r.load_rspec_elements(Clabv1.elements)
#    r.namespaces = Clabv1.namespaces
#    print r.get(RSpecElements.NODE)
    