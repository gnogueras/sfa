'''
Created on 15/02/2014

@author: gerard
'''

#########################################################
# clab_aggregate
#########################################################

    def get_bound_node_from_sliver_rspec(self, node_with_sliver_rspec):
        '''
        Function to get the bound node in which the sliver described in the RSpec
        will be created.
        node_with_sliver_rspec: rspec dict of a node with a sliver
        return: clab node uri
        '''
        pass
    
    
    def get_sliver_ifaces_from_sliver_rspec(self, node_with_sliver_rspec):
        '''
        Function to get the interfaces for the sliver that
        will be created. Requirement for creation i C-Lab.
        node_with_sliver_rspec: rspec dict of a node with a sliver
        return: clab interfaces dict 
        '''
        pass

#####################################
    # URN realted and translation methods
    #####################################
    # NOT USED, using methods from clab_xrn
    
    def urn_to_uri(self, urn):
        '''
        Return the uri that corresponds to the given urn
        '''
        if type_of_urn(urn) == 'node':
            node = self.get_node_by_urn(urn)
            uri = node['uri']
        elif type_of_urn(urn) == 'slice':
            slice = self.get_slice_by_urn(urn)
            uri = slice['uri'] 
        elif type_of_urn(urn) == 'sliver':
            sliver = self.get_sliver_by_urn(urn)
            uri = sliver['uri'] 
        return uri
    
    def get_slice_by_urn(self, urn):
        '''
        Return the slice clab-specific dictionary that corresponds to the 
        given urn
        '''
        slicename=urn_to_slicename(urn)
        return self.driver.testbed_shell.get_slice_by_name(slicename)
    
    
    def get_slice_by_sliver_urn(self, urn):
        '''
        Return the slice clab-specific dictionary that contains the 
        sliver identified by the given urn
        '''
        slivername = urn_to_slivername(urn)
        # slivername = sliceid @ nodeid
        sliver = self.driver.testbed_shell.get_sliver_by_name(slivername)
        slice_uri = sliver['slice']['uri']
        return self.driver.testbed_shell.get_slice_by_uri(slice_uri)
    
    
    def get_node_by_urn(self, urn):
        '''
        Return the node clab-specific dictionary that corresponds to the
        given node urn
        '''
        nodename=urn_to_nodename(urn)
        return self.driver.testbed_shell.get_node_by_name(nodename)
    
    
    def get_sliver_by_urn(self, urn):
        '''
        Return the sliver clab-specific dictionary that corresponds to the
        given sliver urn
        '''
        #sliver_name=sliver_id   --->  slice_id @ node_id
        slivername=urn_to_slivername(urn)
        return self.driver.testbed_shell.get_sliver_by_name(slivername)


#########################################################
# clab_dirver
#########################################################




#########################################################
# clab_xrn
#########################################################





#########################################################
# clab_shell
#########################################################

def get_node_by_uri(self, uri):
    '''
    Return the node clab-specific dictionary that corresponds to the 
    given uri
    '''
    try:
        node = controller.retrieve(uri).serialize()
    except controller.ResponseStatusError:
        node = {}
    return node


def get_slice_by_uri(self, uri):
    '''
    Return the slice clab-specific dictionary that corresponds to the 
    given uri
    '''
    try:
        slice = controller.retrieve(uri).serialize()
    except controller.ResponseStatusError:
        slice = {}
    return slice


def get_sliver_by_uri(self, uri):
    '''
    Return the sliver clab-specific dictionary that corresponds to the 
    given uri
    '''
    try:
        sliver = controller.retrieve(uri).serialize()
    except controller.ResponseStatusError:
        sliver = {}
    return sliver


def get_node_by_name(self, name):
    '''
    Return the node clab-specific dictionary that corresponds to the 
    given name
    '''
    nodes = controller.nodes.retrieve()
    node = [node for node in nodes if node.name==name]
    if node: return node[0].serialize()
    else: return {}


def get_slice_by_name(self, name):
    '''
    Return the slice clab-specific dictionary that corresponds to the 
    given name
    '''
    slices = controller.slices.retrieve()
    slice = [slice for slice in slices if slice.name==name]
    if slice: return slice[0].serialize()
    else: return {}


def get_sliver_by_name(self, name):
    '''
    Return the sliver clab-specific dictionary that corresponds to the 
    given name
    '''
    # name = slice_id @ node_id
    slivers = controller.slivers.retrieve()
    sliver = [sliver for sliver in slivers if sliver.id==name]
    if sliver: return sliver[0].serialize()
    else: return {}


def get_slivers_by_node2(self, node):
        '''
        Function to get the slivers from a specific node
        '''
        sliver_uris = [sliver['uri'] for sliver in node['slivers']]
        slivers = []
        for uri in sliver_uris:
            slivers.append(self.get_sliver_by_uri(uri))
        #slivers = controller.slivers.retrieve().serialize()
        #slivers = [sliver for sliver in slivers if sliver['node']['uri']==node['uri']]
        return slivers
    
    
def get_slivers_by_slice2(self, slice):
    '''
    Function to get the slivers from a specific node
    '''
    sliver_uris = [sliver['uri'] for sliver in slice['slivers']]
    slivers = []
    for uri in sliver_uris:
        slivers.append(self.get_sliver_by_uri(uri))
    #slivers = controller.slivers.retrieve().serialize()
    #slivers = [sliver for sliver in slivers if sliver['slice']['uri']==slice['uri']]
    return slivers


def get_nodes_by_slice2(self, slice):
    '''
    Function to get the nodes from a given slice.
    The nodes that contain slivers belonging to the given slice.
    '''
    slivers = controller.slivers.retrieve().serialize()
    slivers = [sliver for sliver in slivers if sliver['node']['uri']==slice['uri']]
    nodes=[]
    for sliver in slivers:
        nodes.append(controller.retrieve(sliver['node']['uri']).serialize())
    return nodes


def get_slivers_by_node_uri(self, node_uri):
    '''
    Function to get the slivers from a specific node, indicated by its uri
    '''
    slivers = controller.slivers.retrieve().serialize()
    slivers = [sliver for sliver in slivers if sliver['node']['uri']==node_uri]
    return slivers


def get_slivers_by_slice_uri(self, slice_uri):
    '''
    Function to get the slivers from a specific node
    '''
    slivers = controller.slivers.retrieve().serialize()
    slivers = [sliver for sliver in slivers if sliver['slice']['uri']==slice_uri]
    return slivers


def get_nodes_by_slice_uri(self, slice_uri):
    '''
    Function to get the nodes from a given slice.
    The nodes that contain slivers belonging to the given slice.
    '''
    slivers = controller.slivers.retrieve().serialize()
    slivers = [sliver for sliver in slivers if sliver['slice']['uri']==slice_uri]
    nodes=[]
    for sliver in slivers:
        nodes.append(controller.retrieve(sliver['node']['uri']).serialize())
    return nodes

#########################################################
# clab_slices
#########################################################




