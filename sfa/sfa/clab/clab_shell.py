'''
Created on 06/02/2014

@author: gerard
'''

import time
import requests

from orm.api import Api
from orm.resources import Resource

from sfa.clab.clab_exceptions import MalformedURI, UnexistingURI, InvalidURI, ResourceNotFound, OperationFailed

class ClabShell:
    '''
    Simple xmlrpc shell to the C-Lab testbed API instance
    It provides high level methods wrapping the REST API of the testbed
    The class uses the CONFINE-ORM high level library (http://confine-orm.readthedocs.org/)
    '''
    
    def __init__ ( self, config ) :
        global controller
        self.base_uri = 'http://172.24.42.141/api'
        #base_uri=config.base_uri
        controller = Api(self.base_uri) #(config.CLAP_API_URL)
        try:
            controller.retrieve()
        except requests.exceptions.MissingSchema as e:
            raise MalformedURI(self.base_uri, e.message)
        except requests.exceptions.ConnectionError as e:
            raise UnexistingURI(self.base_uri, e.message)
        except ValueError:
            raise InvalidURI(self.base_uri)
            
        # Use of a default user for the C-Lab SFAWrap
        self.username='vct' #config.username
        self.password='vct' #config.password
        self.groupname='vct' #config.group
        #controller.login(config.username, config.password)
        controller.login(self.username, self.password)
        #self.groupname=config.groupname
    
    
    ###############
    # GET METHODS #
    ###############
    
    def get_testbed_info(self):
        '''
        Special funciton to get information from the testbed.
        :returns Dictionary containing information of the testbed
        :rtype dict
        '''
        return {'name': 'clab', 'domain':self.base_uri, 'user':self.username, 'group':self.groupname}
        
    def get_by_uri(self, uri):
        '''
        Function to get any kind of entity by its uri
        
        :param uri: uri of the entity being retrieved
        :type string
        
        :returns C-Lab specific dictionary of the entity
        :rtype dict
        '''
        try:
            resource = controller.retrieve(uri).serialize()
        except controller.ResponseStatusError as e:
            raise ResourceNotFound(uri, e.message)
        except requests.exceptions.MissingSchema as e:
            raise MalformedURI(uri, e.message)
        except requests.exceptions.ConnectionError as e:
            raise UnexistingURI(uri, e.message)
        except ValueError:
            raise InvalidURI(uri)
        return resource
    
    def get_by_uri_no_serialized(self, uri):
        '''
        Function to get any kind of entity by its uri, without serialize
        Return a ORM specific object
        
        :param uri: uri of the entity being retrieved
        :type string
        
        :returns ORM specific object manager
        :rtype orm.manager
        '''
        try:
            resource = controller.retrieve(uri)
        except controller.ResponseStatusError as e:
            raise ResourceNotFound(uri, e.message)
        except requests.exceptions.MissingSchema as e:
            raise MalformedURI(uri, e.message)
        except requests.exceptions.ConnectionError as e:
            raise UnexistingURI(uri, e.message)
        except ValueError:
            raise InvalidURI(uri)
        return resource
    
    def get_nodes(self, filters={}):
        '''
        Function to get the Nodes from the controller.
        The resulting list of nodes can be filtered to get nodes with specific parameters. For example
        if filters={'name':'MyNode'} the function will return a list with all the nodes
        whose name is 'MyNode'
        
        :param filters: dictionary to filter the list of nodes returned 
        :type dict
        
        :returns list of node dictionaries matching the specified filter
        :rtype list 
        '''
        # Get list of dicts (nodes)
        all_nodes = controller.nodes.retrieve().serialize()
        nodes=[]
        nodes.extend(all_nodes)
        for node in all_nodes:
            for key in filters:
                if key not in node or node[key]!=filters[key]:
                    nodes.remove(node)
                    break
        return nodes
    
    def get_slices(self, filters={}):
        '''
        Function to get the Slices from the controller.
        The resulting list of slices can be filtered to get slices with specific parameters. For example
        if filters={'name':'MySlice'} the function will return a list with all the slices
        whose name is 'MySlice'
        Special keys: 'node_uri' (all slices with slivers in that node) NOT SUPPORTED
        
        :param filters: dictionary to filter the list of slices returned 
        :type dict
        
        :returns list of slice dictionaries matching the specified filter
        :rtype list 
        '''
        # Get list of dicts (slices)
        all_slices = controller.slices.retrieve().serialize()
        slices=[]
        slices.extend(all_slices)
        for slice in all_slices:
            for key in filters:
                if key not in slice or slice[key]!=filters[key]: 
                    slices.remove(slice)
                    break
        return slices
    
    
    def get_slivers(self, filters={}):
        '''
        Function to get the Slivers from the controller.
        The resulting list of slivers can be filtered to get slivers with specific parameters. For example
        if filters={'name':'MySliver'} the function will return a list with all the slivers
        whose name is 'MySliver'
        Special keys supported: 'node_uri' (all the slivers of this node)
                                'slice_uri' (all the slivers of this uri)
        
        :param filters: dictionary to filter the list of slivers returned 
        :type dict
        
        :returns list of sliver dictionaries matching the specified filter
        :rtype list 
        '''
        # Get list of dicts (slivers)
        all_slivers=controller.slivers.retrieve().serialize()
        slivers=[]
        slivers.extend(all_slivers)
        for sliver in all_slivers:
            for key in filters:
                if key in ['node_uri', 'slice_uri']:
                    if key == 'node_uri' and sliver['node']['uri']!=filters[key]: 
                        slivers.remove(sliver)
                        break
                    elif key == 'slice_uri' and sliver['slice']['uri']!=filters[key]: 
                        slivers.remove(sliver)
                        break
                else:
                    if key in sliver and sliver[key]==filters[key]: 
                        slivers.append(sliver)
                        break                
        return slivers
    
    
    def get_users(self, filters={}):
        '''
        Function to get the Users from the controller.
        The resulting list of users can be filtered to get users with specific parameters. For example
        if filters={'name':'MyUser'} the function will return a list with all the users
        whose name is 'MyUser'
        
        :param filters: dictionary to filter the list of users returned 
        :type dict
        
        :returns list of user dictionaries matching the specified filter
        :rtype list 
        '''
        # Get list of dicts (users)
        all_users = controller.users.retrieve().serialize()
        users=[]
        users.extend(all_users)
        for user in all_users:
            for key in filters:
                if key not in user or user[key]!=filters[key]: 
                    users.remove(user)
                    break
        return users
    
    
    def get_node_by(self, node_uri=None, node_name=None, node_id=None):
        '''
        Return the node clab-specific dictionary that corresponds to the 
        given keyword argument (uri, name or id)
        One of the parameters must be present.
        
        :param node_uri: (optional) get node with this uri
        :type string
        
        :param node_name: (optional) get node with this name
        :type string
        
        :param node_id: (optional) get node with this id
        :type string
        
        :returns Node dictionary of the specified node
        :rtype dict
        '''
        if node_uri:
            node = self.get_by_uri(node_uri)
        elif node_name:
            nodes = controller.nodes.retrieve()
            node = [node for node in nodes if node.name==node_name]
            if node: 
                node =node[0].serialize()
            else: 
                raise ResourceNotFound(node_name)
        elif node_id:
            nodes = controller.nodes.retrieve()
            if isinstance(node_id, str): node_id = int(node_id)
            node = [node for node in nodes if node.id==node_id]
            if node: 
                node =node[0].serialize()
            else: 
                raise ResourceNotFound(node_id)
        return node
    
    
    def get_slice_by(self, slice_uri=None, slice_name=None, slice_id=None):
        '''
        Return the slice clab-specific dictionary that corresponds to the 
        given keyword argument (uri, name or id)
        One of the parameters must be present.
        
        :param slice_uri: (optional) get slice with this uri
        :type string
        
        :param slice_name: (optional) slice node with this name
        :type string
        
        :param slice_id: (optional) get slice with this id
        :type string
        
        :returns Slice dictionary of the specified slice
        :rtype dict
        '''
        if slice_uri:
            slice = self.get_by_uri(slice_uri)
        elif slice_name:
            slices = controller.slices.retrieve()
            slice = [slice for slice in slices if slice.name==slice_name]
            if slice: 
                slice =slice[0].serialize()
            else: 
                raise ResourceNotFound(slice_name)
        elif slice_id:
            slices = controller.slices.retrieve()
            if isinstance(slice_id, str): slice_id = int(slice_id)
            slice = [slice for slice in slices if slice.id==slice_id]
            if slice: 
                slice =slice[0].serialize()
            else: 
                raise ResourceNotFound(slice_id)
        return slice
    
    
    def get_sliver_by(self, sliver_uri=None, sliver_name=None, sliver_id=None):
        '''
        Return the sliver clab-specific dictionary that corresponds to the 
        given keyword argument (uri, name or id)
        One of the parameters must be present.
        
        :param sliver_uri: (optional) get sliver with this uri
        :type string
        
        :param sliver_name: (optional) get sliver with this name
        :type string
        
        :param sliver_id: (optional) get sliver with this id
        :type string
        
        :returns Sliver dictionary of the specified sliver
        :rtype dict
        '''
        if sliver_uri:
            sliver = self.get_by_uri(sliver_uri)
        elif sliver_name:
            slivers = controller.slivers.retrieve()
            sliver = [sliver for sliver in slivers if sliver.id==sliver_name]
            if sliver: 
                sliver =sliver[0].serialize()
            else: 
                raise ResourceNotFound(sliver_name)
        elif sliver_id:
            slivers = controller.slivers.retrieve()
            sliver = [sliver for sliver in slivers if sliver.id==sliver_id]
            if sliver: 
                sliver =sliver[0].serialize()
            else: 
                raise ResourceNotFound(sliver_id)
        return sliver
    
    
    def get_group_by(self, group_uri=None, group_name=None, group_id=None):
        '''
        Return the group clab-specific dictionary that corresponds to the 
        given keyword argument (uri, name or id)
        One of the parameters must be present.
        
        :param group_uri: (optional) get group with this uri
        :type string
        
        :param group_name: (optional) get group with this name
        :type string
        
        :param group_id: (optional) get group with this id
        :type string
        
        :returns Group dictionary of the specified group
        :rtype dict
        '''
        if group_uri:
            group = self.get_by_uri(group_uri)
        elif group_name:
            groups = controller.groups.retrieve()
            group = [group for group in groups if group.name==group_name]
            if group: 
                group =group[0].serialize()
            else: 
                raise ResourceNotFound(group_name)
        elif group_id:
            groups = controller.groups.retrieve()
            if isinstance(group_id, str): group_id = int(group_id)
            group = [group for group in groups if group.id==group_id]
            if group: 
                group =group[0].serialize()
            else: 
                raise ResourceNotFound(group_id)
        return group
    
    
    def get_slivers_by_node(self, node=None, node_uri=None):
        '''
        Function to get the slivers from a specific node or node uri
        One of the parameters must be present.
        
        :param node_uri: (optional) get slivers of the node indicated by this uri
        :type string
        
        :param node: (optional) get slivers of the node indicated by node dict
        :type dict
        
        :returns List of sliver dictionaries contained in the specified node
        :rtype list
        '''
        # Obtain node dict if argument is node_uri
        if node_uri:
            # Raises exceptions if invalid uri or not found resource
            node = self.get_node_by(node_uri=node_uri)

        # obtain slivers uri of slivers in the node
        sliver_uris = [sliver['uri'] for sliver in node['slivers']]
        # obtian slivers dicts of the slivers in the node
        slivers = []
        for uri in sliver_uris:
            slivers.append(self.get_sliver_by(sliver_uri=uri))
        return slivers
    
    
    def get_slivers_by_slice(self, slice=None, slice_uri=None):
        '''
        Function to get the slivers from a specific slice or slice uri
        One of the parameters must be present.
        
        :param slice_uri: (optional) get slivers of the slice indicated by this uri
        :type string
        
        :param slice: (optional) get slivers of the slice indicated by slice dict
        :type dict
        
        :returns List of sliver dictionaries contained in the specified slice
        :rtype list
        '''
        # Obtain slice dict if argument is slice_uri
        if slice_uri: 
            # Raises exceptions if invalid uri or not found resource
            slice = self.get_slice_by(slice_uri=slice_uri)
        # Obtain sliver uris of slivers in the slice    
        sliver_uris = [sliver['uri'] for sliver in slice['slivers']]
        # Obtain sliver dicts of the slivers in the slice
        slivers = []
        for uri in sliver_uris:
            slivers.append(self.get_sliver_by(sliver_uri=uri))
        return slivers
    
    
    def get_nodes_by_slice(self, slice=None, slice_uri=None):
        '''
        Function to get the nodes from a given slice.
        The nodes that contain slivers belonging to the given slice.
        One of the parameters must be present.
        
        :param slice_uri: (optional) get nodes containing slivers of the slice indicated by this uri
        :type string
        
        :param slice: (optional) get nodes containing slivers of the slice indicated by slice dict
        :type dict
        
        :returns List of node dictionaries containing slivers of the specified slice
        :rtype list
        '''
        # Obtain slivers in the slice
        slivers = self.get_slivers_by_slice(slice=slice, slice_uri=slice_uri)
        # Obtain nodes corresponding to the slivers
        nodes=[]
        for sliver in slivers:
            nodes.append(controller.retrieve(sliver['node']['uri']).serialize())
        return nodes
    
    
    def get_users_by_slice(self, slice=None, slice_uri=None):
        '''
        Function to get the users associated to a given slice.
        The users associated to the slice are those users belonging to the group that owns the sice.
        One of the parameters must be present.
        
        :param slice_uri: (optional) get users associated with the slice indicated by this uri
        :type string
        
        :param slice: (optional) get users associated with the slice indicated by slice dict
        :type dict
        
        :returns List of user dictionaries associated with the specified slice
        :rtype list
        '''
        # Obtain slice dict if argument is slice_uri
        if slice_uri: 
            # Raises exceptions if invalid uri or not found resource
            slice = self.get_slice_by(slice_uri=slice_uri)
        # Obtain group of the slice
        group_uri = slice['group']['uri']
        group = self.get_by_uri(group_uri)
        # Obtain user uris of the user in this group
        user_uris = [user_role['user']['uri'] for user_role in group['user_roles']]
        # Obtain user dicts in this group
        users_of_slice = [self.get_by_uri(user_uri) for user_uri in user_uris]
        return users_of_slice   
        
    
    def get_node_current_state(self, node=None, node_uri=None):
        '''
        Get the current state of the node that corresponds to the 
        given keyword argument (uri or dict)
        One of the parameters must be present.
        
        :param node_uri: (optional) get current state of the node with this uri
        :type string
        
        :param node: (optional) get current state of this node dict
        :type dict
        
        :returns Current state of the specified node
        :rtype string
        '''
        # Get node
        if not node:
            node = self.get_node_by(node_uri=node_uri)
        # Get management network address of the node
        mgmt_net_addr = "http://[%s]/confine/api/node/"%(node['mgmt_net']['addr'])
        # Get and return the state
        # Get Current state may fail if the node is not ready
        try:
            current_state = controller.retrieve(mgmt_net_addr).state
        #except controller.ResponseStatusError:
        except Exception:
            current_state = 'unknown'
        return current_state
            
    
    # NOTE:
    # slice_current_state does not exist
    
    def get_sliver_current_state(self, sliver=None, sliver_uri=None):
        '''
        Get the current state of the sliver that corresponds to the 
        given keyword argument (uri or dict)
        One of the parameters must be present.
        
        :param sliver_uri: (optional) get current state of the sliver with this uri
        :type string
        
        :param sliver: (optional) get current state of this sliver dict
        :type dict
        
        :returns Current state of the specified sliver
        :rtype string
        '''
        # Get sliver
        if not sliver:
            sliver = self.get_sliver_by(sliver_uri=sliver_uri)
        # Get management network address of the sliver
        mgmt_net_addr="http://[%s]/confine/api/slivers/%s/"%(controller.retrieve(sliver['node']['uri']).mgmt_net.addr, sliver['uri'].partition('slivers/')[2])
        # Get and return the state
        # Get current state may fail if the sliver is not ready
        try:
            current_state = controller.retrieve(mgmt_net_addr).state
        #except controller.ResponseStatusError:
        except Exception:
            current_state = 'unknown'
        return current_state
    
    
    def get_available_nodes_for_slice(self, slice_uri):
        '''
        Function that returns the list of available nodes for the given slice.
        Nodes that do not contain a sliver belonging to the given slice are available for that slice.
        (NOTE: one sliver of the same slice per node)
        
        :param slice_uri: get available nodes for the slice indicated by this uri
        :type string
        
        :returns List of node dictionaries of the available nodes for the specified slice
        :rtype list
        '''
        # Get all nodes
        all_nodes = self.get_nodes()
        # Get nodes of the slice        
        nodes_of_slice = self.get_nodes_by_slice(slice_uri=slice_uri) 
        # Get available nodes (nodes in all_nodes and not in nodes_of_slice)
        # avialable_nodes is a list of dictionaries
        available_nodes = [node for node in all_nodes if node not in nodes_of_slice]
        return available_nodes
    
    
    def get_sliver_numeric_id(self, sliver=None, sliver_uri=None, sliver_name=None):
        '''
        Return a unique only-numeric id for the specified sliver
        sliver_uri: http://172.24.42.141/api/slivers/ID
        One of the parameters must be present.
        
        :param sliver_uri: (optional) get unique numeric id of the sliver with this uri
        :type string
        
        :param sliver_name: (optional) get unique numeric id of the sliver with this name
        :type string
        
        :param sliver_id: (optional) get unique numeric id of the sliver with this id
        :type string
        
        :returns Sliver numeric ID as a string
        :rtype string 
        '''
        if not sliver:
            sliver = self.get_sliver_by(sliver_uri=sliver_uri, sliver_name=sliver_name)
        # Get unique numeric if of the sliver
        sliver_numeric_id = sliver['uri'].split('slivers/')[1]
        return sliver_numeric_id
    
    
    def get_sliver_expiration(self, sliver=None, sliver_uri=None, sliver_name=None):
        '''
        Return the expires_on field of the slice that contains the sliver.
        Thus the expiration date of the slice also applies to the sliver.
        One of the parameters must be present. 
        
        :param sliver_uri: (optional) get expiration date of the sliver with this uri
        :type string
        
        :param sliver_name: (optional) get expiration date of the sliver with this name
        :type string
        
        :param sliver_id: (optional) get expiration date of the sliver with this id
        :type string
        
        :returns Sliver expiration date as a string with format 'YYYY-MM-DD'
        :rtype string 
        '''
        if not sliver:
            sliver = self.get_sliver_by(sliver_uri=sliver_uri, sliver_name=sliver_name)
        slice_uri = sliver['slice']['uri']
        return controller.retrieve(slice_uri).expires_on
    
    
    ##################
    # CREATE METHODS #
    ##################
    
    def create_node(self, name, fields):
        '''
        Function to create a node. The fields argument is a dictionary containing at least
        all the required fields for a node to be created.
        Required: name, group, properties, sliver_pub_ipv6, local_iface, sliver_pub_ipv4, arch, sliver_pub_ipv4_range
        optional: description, direct_ifaces
        
        :param fields: dictionary containing all the required fields for the node creation
        :type dict
        
        :returns dictionary containing info of the created node
        :type dict
        
        IMPORTANT NOTE: creation of Nodes is only supported for VCT (Virtual Confine Testbed), but not in the real testbed
                        The create node operation takes 30 sec approx.
        '''

        # Get group or use default one
        group_uri = fields.get('group_uri', None)
        if group_uri:
            group = self.get_by_uri(group_uri)
        else: 
            group = self.get_group_by(group_name=self.groupname)
        
        # Required fields with default value
        properties = fields.get('properties', {})
        sliver_pub_ipv6 = fields.get('sliver_pub_ipv6', 'none')
        sliver_pub_ipv4 = fields.get('sliver_pub_ipv4', 'dhcp')
        sliver_pub_ipv4_range = fields.get('sliver_pub_ipv4_range', '#8')
        local_iface = fields.get('local_iface', 'eth0')
        arch = fields.get('arch', 'i686')
        
        # Optional fields with default value
        description = fields.get('description','')
        direct_ifaces = fields.get('direct_ifaces', [])
        
        # Create node
        try:
            created_node= controller.nodes.create(name=name, group=group, description=description, 
                                direct_ifaces=direct_ifaces, properties=properties, sliver_pub_ipv6=sliver_pub_ipv6, 
                                local_iface=local_iface, arch=arch, sliver_pub_ipv4=sliver_pub_ipv4, sliver_pub_ipv4_range=sliver_pub_ipv4_range)
            created_node.retrieve()
        except controller.ResponseStatusError as e:
            raise OperationFailed('create node', e.message)
        
        # Build Firware
        fw_uri=created_node.get_links()['http://confine-project.eu/rel/controller/firmware']
        controller.post(fw_uri)
        time.sleep(10)
        # Create VM
        vm_uri=created_node.get_links()['http://confine-project.eu/rel/controller/vm']
        controller.post(vm_uri)
        time.sleep(10)
        # Start VM
        controller.patch(vm_uri, {"start": "true"})
        time.sleep(10)
        
        # Set Production State
        created_node.update(set_state='production')
        
        # Return node dictionary
        return created_node.serialize()
    
    
    def create_slice(self, name, group_uri=None, template_uri=None, fields={}, properties={}):
        '''
        Function to create a slice. The parameters are the required arguments for slice creation.
        Some of them have default values. 
        
        :param name: Name of the slice (required)
        :type string
        
        :param group_uri: URI of the group the slice will belong to (has default value) 
        :type string
        
        :param template_uri: URI of the template of the slice (has default value)
        :type string
        
        :param properties: extra properties of the slice
        :type dict
        
        :returns dictionary of the created slice
        :rtype dict     
        '''
        # Get Group and Template
        if group_uri:
            group = self.get_by_uri(group_uri)
        else:
            group = self.get_group_by(group_name=self.groupname)
        if template_uri: 
            template = self.get_by_uri(template_uri)
        else:
            template = controller.templates.retrieve()[1]
            
        # Create slice
        try:
            created_slice = controller.slices.create(name=name, group=group, template=template, properties={})
        except controller.ResponseStatusError as e:
            raise OperationFailed('create slice', e.message)
        # Return slice dictionary
        return created_slice.serialize()
    
        
    def create_sliver(self, slice_uri, node_uri, interfaces_definition=None, properties={}):
        '''
        Function to create a sliver. The parameters are the required arguments for sliver creation.
        Some of them have default values. 
        
        :param slice_uri: URI of the slice the sliver will belong to (required)
        :type string
        
        :param node_uri: URI of the node that will contain the slice (required) 
        :type string
        
        :param interfaces_definition: dictionary defining the interfaces for the created sliver (has default value)
        :type string
        
        :param properties: extra properties of the sliver
        :type dict
        
        :returns dictionary of the created sliver
        :rtype dict  
        '''     
        # Get Slice (no serialized) and Node
        #slice = self.get_slice_by(slice_uri=slice_uri)
        slice = self.get_by_uri_no_serialized(slice_uri)
        node = self.get_node_by(node_uri=node_uri)
        # Interfaces by default
        if not interfaces_definition:
            interfaces_definition = [Resource(name='priv', type='private', nr=0), Resource(name='mgmt0', type='management', nr=1)]       
        # Create sliver
        try:
            created_sliver = slice.slivers.create(node=node, interfaces=interfaces_definition, properties=properties)
        except controller.ResponseStatusError as e:
            raise OperationFailed('create sliver', e.message)
        # Return sliver dict
        return created_sliver.serialize()
    
    
    def create_user(self, username, email=None, description=None, groupname=None, auth_tokens=None):
        '''
        Function to create a user. The parameters are the required arguments for user creation.
        Some of them have default values. 
        NOTE: you need administrator permissions to create users in the testbed.
        
        :param username: URI of the slice the sliver will belong to (required)
        :type string
        
        :param email: URI of the node that will contain the slice (required) 
        :type string
        
        :param description: dictionary defining the interfaces for the created sliver (has default value)
        :type string
        
        :param groupname: extra properties of the sliver
        :type dict
        
        :param auth_tokens: extra properties of the sliver
        :type dict
        
        :returns dictionary of the created sliver
        :rtype dict  
        '''
        # Create/post the new user     
        controller.users.post(data='{ "auth_tokens": "%s",  "description": "%s",  "name": "%s"}'%(auth_tokens, description, username))
        # Get user ORM object 
        user_uri = self.get_users({'name':username})[0]['uri']
        user = self.get_by_uri_no_serialized(user_uri)
        # Get group uri
        if not groupname:
            groupname = self.groupname    
        group_uri = self.get_group_by(group_name=groupname)['uri']
        # Build group roles
        group_roles=[{'is_admin': 'false', 'is_technician': 'false', 'group': {'uri': group_uri}, 'is_researcher': 'true'}]
        # Update user with the group_roles
        user.update(group_roles=group_roles)
        # Return user dict
        return user.serialize()
    
    
    
    ##################
    # UPDATE METHODS #
    ##################
    
    def renew_slice(self, slice_uri):
        '''
        Function that renews the expiration date of the sliver specified by sliver uri argument.
        In C-Lab, expiration date renewals are standard, and the new expiration date cannot be chosen.
        Renew the slice for 30 days. 
        No consecutive renew operations allowed. 30 days from the current day is the maximum expiration date allowed.
        
        :param slice_uri: URI of the slice being renewed
        :type string
        
        :returns boolean indicating if the operation was successful.
        :rtype boolean
        '''
        slice = self.get_by_uri_no_serialized(slice_uri)
        renew_uri=slice.get_links()['http://confine-project.eu/rel/server/do-renew']
        response=controller.post(renew_uri, data='null')
        return True
    
    
    def renew_sliver(self, sliver_uri):
        '''
        Function that renews the expiration date of the slice in which the sliver belongs to.
        Note that this functions will actually renew the expiration date of slivers in the slice.
        In C-Lab, expiration date renewals are standard, and the new expiration date cannot be chosen.
        Renew the slice for 30 days. 
        No consecutive renew operations allowed. 30 days from the current day is the maximum expiration date allowed.
        
        :param sliver_uri: URI of the sliver being renewed
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        sliver = self.get_sliver_by(sliver_uri=sliver_uri)
        return self.renew_slice(sliver['slice']['uri'])
    
    
    def update_node_state(self, node_uri, state):
        '''
        Function that updates the node set_state to the specified state.
        The state argument is a C-Lab specific state (safe, production, failure)
        
        :param node_uri: URI of the node whose state is being updated
        :type string
        
        :param state: new state for the node
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        node = self.get_by_uri_no_serialized(node_uri)
        try:
            node.update(set_state=state)
        except controller.ResponseStatusError as e:
            raise OperationFailed('update node state', e.message)
        return True
    
    
    def update_slice_state(self, slice_uri, state):
        '''
        Function that updates the slice set_state to the specified state.
        The state argument is a C-Lab specific state (register, deploy, start)
        
        :param slice_uri: URI of the slice whose state is being updated
        :type string
        
        :param state: new state for the slice
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        slice = self.get_by_uri_no_serialized(slice_uri)
        try:
            slice.update(set_state=state)
        except controller.ResponseStatusError as e:
            raise OperationFailed('update slice state', e.message)
        return True
    
        
    def update_sliver_state(self, sliver_uri, state):
        '''
        Function that updates the sliver set_state to the specified state.
        The state argument is a C-Lab specific state (register, deploy, start)
        
        :param sliver_uri: URI of the sliver whose state is being updated
        :type string
        
        :param state: new state for the sliver
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        sliver = self.get_by_uri_no_serialized(sliver_uri)
        try:
            sliver.set_state=state
            sliver.save()
        except controller.ResponseStatusError as e:
            raise OperationFailed('update sliver state', e.message)
        return True
    
    
    def update_node(self, node_uri, fields):
        '''
        Function to update the node with the given fields
        
        :param node_uri: URI of the node being updated
        :type string
        
        :param fields: dictionary with new parameters for the node
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        node = self.get_by_uri_no_serialized(node_uri)
        try:
            for key in fields:
                if key=='properties':
                    node.update(properties=fields[key])
                elif key=='arch':
                    node.update(arch=fields[key])
                elif key=='direct_ifaces':
                    node.update(direct_ifaces=fields[key])
                elif key=='local_iface':
                    node.update(local_iface=fields[key])
                elif key=='sliver_pub_ipv6':
                    node.update(sliver_pub_ipv6=fields[key])
                elif key=='sliver_pub_ipv4':
                    node.update(sliver_pub_ipv4=fields[key])
                elif key=='sliver_pub_ipv4_range':
                    node.update(sliver_pub_ipv4_range=fields[key])
                elif key=='name':    
                    node.update(name=fields[key])
                elif key=='description':
                    node.update(description=fields[key])
                elif key=='sliver_mac_prefix':
                    node.update(sliver_mac_prefix=fields[key])
                elif key=='priv_ipv4_prefix':
                    node.update(priv_ipv4_prefix=fields[key])
                elif key=='set_state':
                    node.update(set_state=fields[key])
        except controller.ResponseStatusError as e:
            raise OperationFailed('update node', e.message)
        return True

    
    def update_slice(self, slice_uri, fields):
        '''
        Function to update the slice with the given fields
        
        :param slice_uri: URI of the slice being updated
        :type string
        
        :param fields: dictionary with new parameters for the slice
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        slice = self.get_by_uri_no_serialized(slice_uri)
        try:
            for key in fields:
                if key=='properties':
                    slice.update(properties=fields[key])
                elif key=='vlan_nr':
                    slice.update(vlan_nr=fields[key])
                elif key=='exp_data_uri':
                    slice.update(exp_data_uri=fields[key])
                elif key=='overlay_uri':
                    slice.update(overlay_uri=fields[key])
                elif key=='name':    
                    slice.update(name=fields[key])
                elif key=='description':
                    slice.update(description=fields[key])
                elif key=='set_state':
                    slice.update(set_state=fields[key])
        except controller.ResponseStatusError as e:
            raise OperationFailed('update slice', e.message)
        return True

    
    def update_sliver(self, sliver_uri, fields):
        '''
        Function to update the sliver with the given fields
        
        :param sliver_uri: URI of the sliver being updated
        :type string
        
        :param fields: dictionary with new parameters for the sliver
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        sliver = self.get_by_uri_no_serialized(sliver_uri)
        try:
            for key in fields:
                if key=='properties':
                    sliver.update(properties=fields[key])
                elif key=='interfaces':
                    sliver.update(interfaces=fields[key])
                elif key=='exp_data_uri':
                    sliver.update(exp_data_uri=fields[key])
                elif key=='overlay_uri':
                    sliver.update(overlay_uri=fields[key])
                elif key=='name':    
                    sliver.update(name=fields[key])
                elif key=='description':
                    sliver.update(description=fields[key])
                elif key=='template':
                    sliver.update(template=fields[key])
                elif key=='set_state':
                    sliver.update(set_state=fields[key])
        except controller.ResponseStatusError as e:
            raise OperationFailed('update sliver', e.message)
        return True


    def update_user(self, user_uri, fields):
        '''
        Function to update the user with the given fields
        
        :param user_uri: URI of the user being updated
        :type string
        
        :param fields: dictionary with new parameters for the user
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        user = self.get_by_uri_no_serialized(user_uri)
        print "shell.update_user called with user_uri=%s and fields="%(user_uri)
        print fields
        try:
            for key in fields:
                if key=='name':    
                    user.update(name=fields[key])
                elif key=='description':
                    user.update(description=fields[key])
                elif key=='is_active':
                    user.update(is_active=fields[key])
                elif key=='group_roles':
                    user.update(group_roles=fields[key])
        except controller.ResponseStatusError as e:
            raise OperationFailed('update user', e.message)
        return True


    ##################
    # DELETE METHODS #
    ##################
    
    def delete(self, uri):
        '''
        General function to delete any kind of entity (node, sliver, slice)
        identified by the fiven uri
        
        :param uri: URI of the entity being deleted
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        try:
            controller.destroy(uri)
        except controller.ResponseStatusError as e:
            raise OperationFailed('delete', e.message)
        return True    

    
    def delete_node(self, node_uri):
        '''
        Function to delete the node specified by the node uri argument
        It deletes any sliver contained in this node
        
        :param node_uri: URI of the node being deleted
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        try:
            controller.destroy(node_uri)
        except controller.ResponseStatusError as e:
            raise OperationFailed('delete node', e.message)
        return True    
        
        
    def delete_slice(self, slice_uri):
        '''
        Function to delete the slice specified by the slice uri argument
        It deletes any sliver contained in this slice
        
        :param slice_uri: URI of the slice being deleted
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        try:
            controller.destroy(slice_uri)
        except controller.ResponseStatusError as e:
            raise OperationFailed('delete slice', e.message)
        return True    
        
        
    def delete_sliver(self, sliver_uri):
        '''
        Function to delete the sliver specified by the sliver uri argument
        
        :param sliver_uri: URI of the sliver being deleted
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        try:
            controller.destroy(sliver_uri)
        except controller.ResponseStatusError as e:
            raise OperationFailed('delete sliver', e.message)
        return True    
    
  
    #################
    # OTHER METHODS #
    #################      
    def reboot_node(self, node_uri):
        '''
        Function to reboot the node specified by the node uri argument.
        
        :param node_uri: URI of the node being rebooted
        :type string
        
        :returns boolean indicating if the operation was successful
        :rtype boolean
        '''
        node = self.get_by_uri_no_serialized(node_uri)
        reboot_uri=node.get_links()['http://confine-project.eu/rel/server/do-reboot']
        response=controller.post(reboot_uri, data='null')
        return response.ok           
    
       
