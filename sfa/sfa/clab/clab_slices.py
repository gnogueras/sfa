'''
Created on 06/02/2014

@author: gerard
'''
import random


from sfa.rspecs.rspec import RSpec
from sfa.util.sfalogging import logger
from sfa.util.sfatime import utcparse, datetime_to_epoch
from sfa.util.xrn import Xrn, get_leaf, get_authority, urn_to_hrn


from sfa.clab.clab_xrn import urn_to_uri, urn_to_slicename, get_slice_by_urn

class ClabSlices:
    '''
    Class that checks the Slices and Nodes in the operations of the AM.
    It verifies that requested slices,nodes exist.
    '''

    def __init__(self, driver):
        self.driver = driver
        
    
    def verify_slice(self, slice_urn, credentials, creation_flag, options={}):
        '''
        Function that verifies a slice given by its urn.
        It checks if the slice exists. If so, returns the C-lab slice dict.
        If slice does not exist and creation_flag is true, it creates a new slice
        with default parameters and returns the C-lab slice dict.
        If slice does not extist and creation_falg is false, it returns an empty dict
        or raises an exception.
        
        :param slice_urn: URN of the slice that is being verified
        :type string
        
        :param credentials: GENI credentials of the caller and slices 
        :type list
        
        :param creation_flag: flag indicating if the creation of slices is allowed
            in this function
        :type boolean
        
        :param options: various options.
        :type dictionary
        
        :returns C-lab slice dict
        :rtype dict
        '''
        # Get slice
        slice = get_slice_by_urn(self.driver, slice_urn)
        if slice:
            # Slice exist
            # Set the set_state to Register because the slice will be modified
            self.driver.testbed_shell.update_slice_state(slice['uri'], 'register')
            return slice
        
        else:
            # Slice does not exist
            if creation_flag:
                # create Slice
                slicename = urn_to_slicename(slice_urn)
                # TODO: get group uri from credentials
                group_uri='http://172.24.42.141/api/groups/1'
                created_slice = self.driver.testbed_shell.create_slice(slicename, group_uri)
                return created_slice
            else:
                # Raise error or return empty dict
                return {}

    
    
    def verify_node(self, slice_urn, node_element, credentials, creation_flag, options={}):
        '''
        Function that verifies a single node by its NodeElement RSpec description. The verification 
        consists of checking if the given node is ready to allocate an sliver of the indicated slice
        The NodeElement can specify a specific bound node or not.
        If bound node specified:
            It checks if the node exist. If so, it returns a C-lab node dict.
            It checks that the node is available for the slice, i.e. it does not contain slivers for this slice.
            It deletes old slivers in the slice if any. 
            If the node does not exist and creation_flag is true, it creates a new node with
            default parameters and return its C-Lab dict.
            If the node does not exist and creation_flag is false, it returns an empty dict or raises an exception.
        If unbound node:
            It selects randomly one available node for the slice and returns its C-lab dict.
        
        :param slice_urn: URN of the slice that will contain the sliver
        :type string
        
        :param node_element: node dictionary of the node being checked
        :type dict 
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param creation_flag: flag indicating if the creation of nodes is allowed
            in this function
        :type boolean
        
        :param options: various options.
        :type options: dictionary
        
        :returns C-lab slice dict
        :rtype dict 
               
        IMPORTANT NOTE: Creation of Nodes is only supported for VCT (Virtual Confine Testbed), but not
        for real testbed. By default, creation_flag=false
        '''
        # Get slice uri
        slice_uri = urn_to_uri(self.driver, slice_urn)
        
        if node_element['component_id'] and node_element['component_manager_id'] in node_element: 
            # Bound node specified
            # component_id = URN of the node | component_manager_id = URN of the authority
            node_uri = urn_to_uri(self.driver, node_element['component_id'])
            node = self.driver.testbed_shell.get_node_by_uri(node_uri)
            
            if node:
                # Required bound exists
                # node available for the slice?
                if node not in self.driver.testbed_shell.get_available_nodes_for_slice(slice_uri):
                    # Node already contains an sliver for this slice
                    # Delete old sliver
                    old_sliver = self.driver.testbed_shell.get_slivers({'node_uri':node_uri, 'slice_uri':slice_uri})[0]
                    self.driver.testbed_shell.delete_sliver(old_sliver['uri'])
                # Node is available
                return node
            
            else:
                # Required bound node does not exist
                if creation_flag:
                    # Create node
                    node_name = node_element['client_id'] # cient_id = node name
                    # TODO: get group uri from credentials
                    group_uri='http://172.24.42.141/api/groups/1'
                    created_node = self.driver.testbed_shell.create_node({'name':node_name, 'group_uri':group_uri})
                    return created_node
                
                else:
                    # Return empty dict, raise an exception
                    return {} 
                
        else: 
            # Bound node not specified
            available_nodes = self.driver.testbed_shell.get_available_nodes_for_slice(slice_uri)
            if available_nodes:
                randomly_selected = random.randint(0, len(available_nodes)-1)
                node = available_nodes[randomly_selected]
            else:
                node = {}
            return node
    

    
    

                 
        
    
    
    
