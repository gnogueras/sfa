'''
Created on 06/02/2014

@author: gerard
'''

from sfa.rspecs.elements.granularity import Granularity
from sfa.rspecs.elements.hardware_type import HardwareType
from sfa.rspecs.elements.lease import Lease
from sfa.rspecs.elements.login import Login
from sfa.rspecs.elements.sliver import Sliver
from sfa.rspecs.rspec import RSpec
from sfa.rspecs.version_manager import VersionManager
from sfa.storage.model import SliverAllocation
from sfa.util.sfalogging import logger
from sfa.util.sfatime import utcparse, datetime_to_string
from sfa.util.xrn import Xrn, hrn_to_urn, urn_to_hrn
from sfa.rspecs.elements.node import NodeElement

import datetime

# local imports from the Project
#from rspecs.elements.versions.clabNode import ClabNode
from sfa.clab.clab_xrn import type_of_urn, urn_to_slicename, slicename_to_urn,\
    hostname_to_urn, urn_to_nodename, urn_to_slivername, slivername_to_urn
from sfa.clab.clab_xrn import urn_to_uri, get_node_by_urn, get_slice_by_urn, get_sliver_by_urn, get_slice_by_sliver_urn
from sfa.clab.clab_slices import ClabSlices


class ClabAggregate:
    """
    Aggregate Manager class for C-Lab. 
    GENI AM API v3
    """
    
    def __init__(self, driver):
        self.driver = driver
        self.AUTHORITY = driver.AUTHORITY
        self.AUTOMATIC_SLICE_CREATION = driver.AUTOMATIC_SLICE_CREATION
        self.AUTOMATIC_NODE_CREATION = driver.AUTOMATIC_NODE_CREATION
        
        
        
    ##################################
    # GENI AM API v3 METHODS
    ##################################
            
    def get_version(self):
        """
        Returns a dictionary following the GENI AM API v3 GetVersion struct. 
        It contains information about this aggregate manager implementation, 
        such as API and RSpec versions supported.
        
        :returns: dictionary implementing GENI AM API v3 GetVersion struct
        :rtype: dict
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#GetVersion

        """
        # Version by default: GENI 3
        version_manager = VersionManager()
        
        # int geni_api 
        geni_api = int(version_manager.get_version('GENI 3').version)
        
        # struct code
        code = dict(geni_code=0)
        
        # struct value
        value = dict()
        value['geni_api'] = int(version_manager.get_version('GENI 3').version)
        value['geni_api_versions'] = dict([(version_manager.get_version('GENI 3').version, "This server's AM API absolute URL")])
        value['geni_request_rspec_versions'] = [version.to_dict() for version in version_manager.versions if (version.content_type in ['*', 'request'] and version.type=='GENI')]
        value['geni_ad_rspec_versions'] = [version.to_dict() for version in version_manager.versions if (version.content_type in ['*', 'ad'] and version.type=='GENI')]
        value['geni_credential_types'] = [{'geni_type': 'geni_sfa', 'geni_version' : '3'}] ##???????????????????????????? CHECK
        
        # output
        output = None
        
        return dict([('geni_api', geni_api), ('code', code), ('value', value), ('output', output)])
    
    
    
    def list_resources(self, credentials={}, options={}):
        """
        Returns an advertisement Rspec of available resources at this
        aggregate. This Rspec contains a resource listing along with their
        description, providing sufficient information for clients to be able to
        select among available resources.
        
        :param credentials: GENI credentials of the caller 
        :type credentials: list

        :param options: various options. The valid options are: {boolean
            geni_compressed <optional>; struct geni_rspec_version { string type;
            #case insensitive , string version; # case insensitive}} . The only
            mandatory options if options is specified is geni_rspec_version.
        :type options: dictionary

        :returns: On success, the value field of the return struct will contain
            a geni.rspec advertisment RSpec
        :rtype: Rspec advertisement in xml.

        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3/CommonConcepts#RSpecdatatype
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#ListResources
        """

        version_manager = VersionManager()
        version = version_manager.get_version('GENI 3')        
        rspec_version = version_manager._get_version(version.type, version.version, 'ad')
        rspec = RSpec(version=rspec_version, user_options=options)        
        
        # List resources: available nodes and/or slices??
        # belonging to the aggregate
        # and the user??? 
        # all the users can create slices in any node?
        # the users can create slivers in their own slices?
        
        # username can be obtained form the credential
        
        #Geni state in options?
        state=None
        if options.get('available'): state='available'
                
        # Function get nodes
        nodes = self.get_nodes_by_geni_state(state)

        # Translate to Rspec
        rspec_nodes = []
        for node in nodes:
            rspec_nodes.append(self.clab_node_to_rspec_node(node))
            
        # Function get slices
        #slices = self.get_slices_by_geni_state(state)

        rspec.version.add_nodes(rspec_nodes)        
        return rspec.toxml()
    
    
        
    def describe(self, urns, credentials={}, options={}):
        """
        Retrieve a manifest RSpec describing the resources contained by the
        named entities, e.g. a single slice or a set of the slivers in a slice.
        This listing and description should be sufficiently descriptive to allow
        experimenters to use the resources.

        :param urns: list of slice URNs or sliver URNs that belong to the same slice, whose 
            resources will be described
        :type urns: list  of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. the valid options are: {boolean
            geni_compressed <optional>; struct geni_rspec_version { string type;
            #case insensitive , string version; # case insensitive}}
        :type options: dictionary

        :returns On success returns the following dictionary:
        {
         geni_rspec: <geni.rspec, a Manifest RSpec>
         geni_urn: <string slice urn of the containing slice> 
         geni_slivers: list of dict 
                         { geni_sliver_urn: <string sliver urn>, 
                           geni_expires:  <dateTime.rfc3339 allocation expiration string, as in geni_expires from SliversStatus>,
                           geni_allocation_status: <string sliver state - e.g. geni_allocated or geni_provisioned >, 
                           geni_operational_status: <string sliver operational state>, 
                           geni_error: <optional string. The field may be omitted entirely but may not be null/None,
                                        explaining any failure for a sliver.>
                         }
        }
        :rtype dict

        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Describe

        """
        print "CLAB AGGREGATE DESCRIBE METHOD"
        
        version_manager = VersionManager()
        version = version_manager.get_version('GENI 3')        
        rspec_version = version_manager._get_version(version.type, version.version, 'manifest')
        rspec = RSpec(version=rspec_version, user_options=options)  
        
        # Check that urn argument is a list (not a string)
        if isinstance(urns, str): urns = [urns] 
        
        if(type_of_urn(urns[0])=='slice'):
            # urns = single slice urn 
            # First urn belongs to slice. Other urns of the list will be ignored
            # There should be just one urn if the type is slice
            geni_urn=urns[0]
            # Get dictionary slice from urn
            slice=get_slice_by_urn(self.driver, geni_urn)
            # Get slivers of the slice (list of sliver dictionaries)
            slivers=self.driver.testbed_shell.get_slivers_by_slice(slice=slice)
            # Get nodes of the slice (list of nodes dictionary)
            nodes=self.driver.testbed_shell.get_nodes_by_slice(slice=slice)
            
        elif(type_of_urn(urns[0])=='sliver'):
            # urns = set of slivers urns in a single slice
            # Get the slice from one of the urn-sliver (dictionary slice)
            slice=get_slice_by_sliver_urn(self.driver, urns[0])
            geni_urn=slicename_to_urn(self.AUTHORITY, slice['name'])
            # Get slivers from the urns list (list of slivers dictionary)
            slivers=[]
            for urn in urns:
                slivers.append(get_sliver_by_urn(self.driver, urn))
            # Get nodes of the slice (list of nodes dictionary)
            nodes=self.driver.testbed_shell.get_nodes_by_slice(slice=slice)   
            
        # Prepare Return struct
        # geni_rpec. Translate nodes to rspec
        rspec_nodes = []
        for node in nodes:
            rspec_nodes.append(self.clab_node_to_rspec_node(node))
        rspec.version.add_nodes(rspec_nodes)
        
        # geni_slivers. Translate to geni (list of geni sliver dicts)
        geni_slivers = []
        for sliver in slivers:
            geni_slivers.append(self.clab_sliver_to_geni_sliver(sliver))
        
        return {'geni_urn': geni_urn,
                'geni_rspec': rspec.toxml(),
                'geni_slivers': geni_slivers}
        
            
    def allocate(self, slice_urn, rspec_string, expiration, credentials={}, options={}):
        '''
        Function to allocate/reserve the resources described in the rspec_string for a sliver 
        that will belong to the slice specified by the slice_urn argument.
        
        :param slice_urn: URN of the slice in which the resources will be allocated
        :type slice_urn: string
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param rspec_string: string that contains a XML RSpec describing the resources
            that will be allocated in the givne slice
        :type string
        
        :param expiration: string that contains the expiration date of the allocated resources
        :type string
        
        :param options: various options.
        :type options: dictionary
        
        :returns Returns the following struct:
        {
             "geni_slivers" -> [
                 {
                     "geni_sliver_urn" -> "urn:publicid:IDN+wall2.ilabt.iminds.be+sliver+2576",
                     "geni_allocation_status" -> "geni_allocated",
                     "geni_expires" -> "2014-02-10T11:39:28Z"
                }
             ],
             "geni_rspec" -> rspec string
        }
        :rtype dict
    
        NOTE: ALLOCATE (GENI) = REGISTER (C-LAB)
              Create slivers in Register state. (by default, takes state from slice)
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Allocate      
        
        '''
        # ClabSlices class is a checker for nodes and slices
        checker = ClabSlices(self.driver)
        
        # Verify slice exist. Return slice in Register state (to be modified)
        slice = checker.verify_slice(slice_urn, credentials, self.AUTOMATIC_SLICE_CREATION, options={})
        
        # parse RSpec (if rspec_string argument)
        rspec = RSpec(rspec_string)
        # nodes in which the slivers will be created (list of dict)
        nodes_with_slivers = rspec.version.get_nodes_with_slivers()
        # ignore slice attributes...
        requested_attributes = rspec.version.get_slice_attributes()
        
        # Translate sliver RSpecs to C-Lab slivers
        # Each element node_with_sliver will create a sliver belonging to the slice in the corresponding node
        for node_with_sliver in nodes_with_slivers:            
            # Verify the required nodes
            bound_node = checker.verify_node(slice_urn, node_with_sliver, credentials, 
                                             self.AUTOMATIC_NODE_CREATION, options)
            # interfaces_definition
            interfaces = node_with_sliver['interfaces'] 
            interfaces_definition=[]
            for interface in interfaces:
                # Get the interface name  (client_id = MySliverName:IfaceName)
                name = interface['client_id']
                if ':' in name: name = name.split(':')[1]
                interface_definition = dict([('name', name),('type', interface['role']),('nr', int(interface['interface_id']))])
                interfaces_definition.append(interface_definition)
            
            # properties
            properties={}
            
            # create the sliver
            created_sliver = self.driver.testbed_shell.create_sliver(slice['uri'], bound_node['uri'], 
                                                                     interfaces_definition, properties)
        # prepare return struct 
        return self.describe([slice_urn], credentials, options)

    
    def renew(self, urns, expiration_time, credentials={}, options={}):
        '''
        Request that the named slivers be renewed, with their expiration date extended.
        However, the expiration_time argument is ignore since in C-Lab, renewals are standard 
        and the expiration date is set to 30 days from the current date (maximum)
        In C-Lab the entities that are renewed are the SLICES, but not the SLIVERS.
        Note that renew a slice automatically renews all the slivers contained in that slice.
        Therefore, urns argument can contain sliver urns or slice urns. (either slivers or slices)
        In case of containing sliver urns, the slice in which the sliver is contained will be renewed.
        Note again that renewing a slice it automatically renews all the slivers of the slice.
        
        :param urns: list of slice URNs or sliver URNs that belong to the same slice, whose 
            resources will be described
        :type urns: list  of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. the valid options are: {boolean
            geni_best_effort <optional>} If false, it specifies whether the client 
            prefers all included slivers/slices to be renewed or none. 
            If true, partial success if possible
        :type options: dictionary
        
        :returns On success, returns a list of dict:
        [
            {    geni_sliver_urn: string
                 geni_allocation_status: string
                 geni_operational_status: string
                 geni_expires: string
            }
        ]
        :rtype list of dict
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Renew
        
        '''
        # Get geni_best_effort option
        geni_best_effort = options.get('geni_best_effort', 'true').lower()
        
        # Check that urn argument is a list (not a string)
        if isinstance(urns, str): urns = [urns]
        
        # SLIVERS
        if type_of_urn(urns[0])=='sliver':    
            # Get uris of slivers from the urns list
            uris = [urn_to_uri(self.driver, urn) for urn in urns]
            for uri in uris:
                ok=self.driver.testbed_shell.renew_sliver(uri)
                if not geni_best_effort and not ok: break
        
        # SLICES
        elif type_of_urn(urns[0])=='slice':
            # Get uris of slivers from the urns list
            uris = [urn_to_uri(self.driver, urn) for urn in urns]
            for uri in uris:
                ok=self.driver.testbed_shell.renew_slice(uri)
                if not geni_best_effort and not ok: break
       
        # Return struct (geni_slivers field of Describe method)
        description = self.describe(urns, 'GENI 3')
        return description['geni_slivers']

    
    def provision(self, urns, credentials={}, options={}):
        '''
        Request for provisioning the the indicated slivers/slices, so their state become geni_provisioned 
        and they may possibly be geni_ready for experimenter use.
        The urns argument indicates either the slivers or slices that have to be provisioned.
        Note that the slice status has priority over the sliver status.
        
        :param urns: list of slice URNs or sliver URNs that belong to the same slice, whose 
            resources will be provisioned
        :type urns: list  of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. the valid options are: {string
            geni_rspec_version <optional>} It indicates the verson of RSpec 
        :type options: dictionary
        
        :returns On success, returns the following dict:
        {
            geni_rspec: RSpec manifest (string)
            geni_slivers: [
                            {    geni_sliver_urn: string
                                 geni_allocation_status: string
                                 geni_operational_status: string
                                 geni_expires: string
                            }, 
                            ...
                          ]
        }
        The returned manifest covers only new provisioned slivers.
        :rtype dict 
        
        NOTE: PROVISION (GENI) = DEPLOY (C-LAB)
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Provision
        
        '''
        # Get geni_best_effort option
        geni_best_effort = options.get('geni_best_effort', 'true').lower()
        
        # Check that urn argument is a list (not a string)
        if isinstance(urns, str): urns = [urns]
        
        # SLIVER
        if type_of_urn(urns[0])=='sliver':    
            # Get uris of slivers from the urns list
            uris = [urn_to_uri(self.driver, urn) for urn in urns]
            for uri in uris:
                self.driver.testbed_shell.update_sliver_state(uri, 'deploy')
            
            # MANAGEMENT FROM SLICE
            # Get uris of slivers from the urns list
            #uris = [urn_to_uri(self.driver, urn) for urn in urns]
            # Set sliver state to 'from_slice'
            #for uri in uris:
            #    self.driver.testbed_shell.update_sliver_state(uri, 'null')    
            # Get the slice uri of the slivers
            #slice_uri = self.driver.testbed_shell.get_sliver_by(sliver_uri=uris[0])['slice']['uri']
            # Set slice state to 'deploy'
            #self.driver.testbed_shell.update_slice_state(slice_uri, 'deploy')  
                
        
        # SLICE
        elif type_of_urn(urns[0])=='slice':
            # Get uris of slices from the urns list
            uris = [urn_to_uri(self.driver, urn) for urn in urns]
            for uri in uris:
                self.driver.testbed_shell.update_slice_state(uri, 'deploy')
        
        # Prepare and return the struct (use describe function)   
        version_manager = VersionManager()
        rspec_version = version_manager.get_version('GENI 3')
        return self.describe(urns, credentials, options)
    
    
    def status (self, urns, credentials={}, options={}):
        '''
        Function to get the status of a sliver or slivers belonging to a single slice at the given aggregate.
        
        :param urns: list of slice URNs or sliver URNs that belong to the same slice, whose 
            status will be retrieved
        :type urns: list  of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. 
        :type options: dictionary
        
        :returns On success returns the following:
        {
            geni_urn: slice URN
            geni_slivers: [
                            {    geni_sliver_urn: sliver URN
                                 geni_allocation_status: string
                                 geni_operational_status: string
                                 geni_expires: string
                            },
                            ...
                          ]
        }
        :rtype dict
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Status
        
        '''
        description = self.describe(urns, credentials, options)
        status = {'geni_urn': description['geni_urn'],
                  'geni_slivers': description['geni_slivers']}
        return status
        

    def perform_operational_action(self, urns, action, credentials={}, options={}):
        '''
        Perform the named operational action on the named slivers, possibly changing
        the geni_operational_staus of the slivers. 
        
        :param urns: list of slice URNs or sliver URNs that belong to the same slice, that will 
            be affected by the operational action
        :type urns: list  of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. the valid options are: 
            {boolean geni_best_effort <optional>} 
            False: action applies to all slivers equally or none
            True: try all slivers even if some fail
        :type options: dictionary
        
        :returns On success returns the following:
              [
                    {    geni_sliver_urn: sliver URN
                         geni_allocation_status: string
                         geni_operational_status: string
                         geni_expires: string
                         geni_resource_status: optional string
                         geni_error: optional string
                    },
                    ...
              ]
        :rtype list of dict
        
        Supported actions: geni_start, geni_restart, geni_stop 
        geni_start = set_state to start in the sliver/slice
        geni_restart = reboot node that contains the sliver
        geni_stop = not supported... (delete slice?)
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Status
        
        '''
        # Get geni_best_effort option
        geni_best_effort = options.get('geni_best_effort', 'true').lower()
        
        # Check that urn argument is a list (not a string)
        if isinstance(urns, str): urns = [urns]
        
        # Discover if urns is a list of sliver urns or slice urns
        if type_of_urn(urns[0])=='sliver': is_sliver_list=1 # urns is a sliver list
        else: is_sliver_list=0 # urns is a slice list
        
        # Get uris of slivers/slices from the urns list
        uris = [urn_to_uri(self.driver, urn) for urn in urns]
        
        if action in ['geni_start', 'start']:
            # Start sliver or slice
            # SLIVER
            if is_sliver_list:    
                for uri in uris:
                    self.driver.testbed_shell.update_sliver_state(uri, 'start')
            # SLICE
            else:
                for uri in uris:
                    self.driver.testbed_shell.update_slice_state(uri, 'start')
        
        elif action in ['geni_restart', 'restart']:
            # Restart node that contains the slivers
            # SLIVER
            if is_sliver_list: 
                for uri in uris:
                    # Reboot node containing each sliver
                    node_uri = self.driver.testbed_shell.get_sliver_by(sliver_uri=uri)['node']['uri']
                    self.driver.testbed_shell.reboot_node(node_uri)
            # SLICE
            else:
                for uri in uris:
                    # Get nodes of the slice
                    nodes_of_slice = self.driver.testbed_shell.get_nodes_by_slice(slice_uri=uri)
                    # Reboot all the nodes of the slice
                    for node in nodes_of_slice:
                        self.driver.testbed_shell.reboot_node(node['uri'])
        
        elif action in ['geni_stop', 'stop']:
            # Not supported
            # Delete slivers/slices or set them to deploy?
            # SLIVER
            if is_sliver_list: 
                for uri in uris:
                    # Delete slivers in the list
                    #self.driver.testbed_shell.delete_sliver(uri)
                    # Set sliver state to deploy: 
                    self.driver.testbed_shell.update_sliver_state(uri, 'deploy')
            # SLICE
            else:
                for uri in uris:
                    # Delete slices in the list
                    #self.driver.testbed_shell.delete_slice(uri)
                    # Set sliver state to deploy: 
                    self.driver.testbed_shell.update_slice_state(uri, 'deploy')
                    
        # Return struct (geni_slivers field of Describe method)
        description = self.describe(urns, credentials, options)
        return description['geni_slivers']    
                
        # Prepare and return the struct (use describe function)   
        #version_manager = VersionManager()
        #rspec_version = version_manager.get_version('GENI 3'options['geni_rspec_version'])
        #return self.describe(urns, rspec_version, options=options)
    
        
    
    def delete(self, urns, credentials={}, options={}):
        '''
        Delete the named slivers, making them geni_unallocated
        The urns argument can be a list of slivers urns (belonging to the same slice)
        or a single slice urn, so the operation will affect all the slivers in the slice
        
        :param urns: list of slice URNs or sliver URNs that belong to the same slice, which will 
            be deleted
        :type urns: list of strings
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. 
        :type options: dictionary
        
        :returns list of dicts of the slivers that have been deleted
            [
                {    geni_sliver_urn: string
                     geni_allocation_status: 'geni_unallocated'
                     geni_expires: string
                },
                ...
            ]
        :rtype list of dict
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Delete
        
        '''
        # Get geni_best_effort option
        geni_best_effort = options.get('geni_best_effort', 'true').lower()
        
        # Return list
        deleted_slivers = []
                
        # Discover if urns is a list of sliver urns or slice urns
        # SLIVER
        if type_of_urn(urns[0])=='sliver':
            # For each urn of the list
            for urn in urns:
                # Obtain sliver uri and complete return struct
                sliver_uri = urn_to_uri(self.driver, urn)
                slice_uri = self.driver.testbed_shell.get_sliver_by(sliver_uri=sliver_uri)['slice']['uri']
                expires_on = self.driver.testbed_shell.get_slice_by(slice_uri=slice_uri)['expires_on']
                deleted_sliver = dict([('geni_sliver_urn', urn), ('geni_allocation_status', 'geni_unallocated'), ('geni_expires', expires_on)])
                deleted_slivers.append(deleted_sliver)
                # Delete the sliver
                self.driver.testbed_shell.delete(sliver_uri)
        # SLICE
        elif type_of_urn(urns[0])=='slice':
            # For each slice urn of the list
            for urn in urns:
                slice_uri = urn_to_uri(self.driver, urn)
                expires_on = self.driver.testbed_shell.get_slice_by(slice_uri=slice_uri)['expires_on']
                slivers = self.driver.testbed_shell.get_slivers_by_slice(slice_uri=slice_uri)
                # For each sliver of the slice
                for sliver in slivers:
                    # Complete return struct
                    sliver_urn = slivername_to_urn(self.AUTHORITY, sliver['id'])
                    sliver_uri = urn_to_uri(self.driver, sliver_urn)
                    deleted_sliver = dict([('geni_sliver_urn', sliver_urn), ('geni_allocation_status', 'geni_unallocated'), ('geni_expires', expires_on)])
                    deleted_slivers.append(deleted_sliver)
                    # Delete the sliver
                    self.driver.testbed_shell.delete(sliver_uri)
        
        return deleted_slivers
          
    
    def shutdown(self, slice_urn, credentials={}, options={}):
        '''
        Perform an emeregency shutdown on the slivers in the given slive at this aggregate. 
        Resources should be taken offline such that experimenter access is cut off. 
        The slivers are shut down but remain available for further forensics.
        
        No direct translation to C-Lab. The function will set the set_state of the slice to Register,
        so the resources are reserved but offline. Therefore, all the slivers of the slice will eventually be
        in Registered state.
        
        :param slice_urn: URN of the slice whose slivers will be shutdown
        :type slice_urn: string
        
        :param credentials: GENI credentials of the caller and slices 
        :type credentials: list
        
        :param options: various options. 
        :type options: dictionary
        
        :return True
        :rtype boolean
        
        .. seealso:: http://groups.geni.net/geni/wiki/GAPI_AM_API_V3#Shutdown
        
        '''
        slice_uri = urn_to_uri(self.driver, slice_urn)
        self.driver.testbed_shell.update_slice_state(slice_uri, 'register')
        # Return true indicating success
        return 1
    
    
    ############################################################################################
    
    ##################################
    # AUXILIARY METHODS AM
    ##################################
    # Methods for AM based on 
    # URN/HRN (SFA standard)
    # GENI API
    ##################################
    
    #####################################
    # GENI realted and translationmethods
    #####################################
    
    def clab_sliver_to_geni_sliver(self, sliver):
        '''
        Method that receives a clab-specific dictionary describing the sliver
        and returns a dictionary describing the sliver with geni format.
        Function used in Describe
        The fields of the geni_sliver:
            geni_sliver_urn
            geni_expires
            geni_allocation_status
            geni_operational_status
        
        :param sliver: C-lab specific dictionary of a sliver
        :type dict
        
        :returns GENI specific dictionary of a sliver
        :rtype dict
        '''
        # Get fields of the geni sliver dictionary
        
        # Get sliver urn
        geni_sliver_urn = slivername_to_urn(self.AUTHORITY, sliver['id'])
        
        # Get expiration date of the sliver (RFC 3339 format)
        # Get string containing the expires_on field of the slice containing the sliver
        sliver_expires_on = self.driver.testbed_shell.get_sliver_expiration(sliver=sliver)
        # Create a datetime object
        dt = self.get_datetime_from_clab_expires(sliver_expires_on)
        geni_expires = datetime_to_string(dt)
        
        # Get current state of the sliver
        sliver_current_state = self.driver.testbed_shell.get_sliver_current_state(sliver=sliver)
        # Fill geni states
        geni_allocation_status = self.clab_state_to_geni_state(sliver_current_state, allocation=True)
        geni_operational_status = self.clab_state_to_geni_state(sliver_current_state, operational=True)
        
        # Create and fill geni sliver dictionary
        geni_sliver = {'geni_sliver_urn':geni_sliver_urn, 'geni_expires':geni_expires, 
                       'geni_allocation_status':geni_allocation_status, 'geni_operational_status':geni_operational_status}
        return geni_sliver 
    
    
    def get_datetime_from_clab_expires(self, sliver_expires_on):
        '''
        Function to get a datetime object from the string parameter sliver_expires_on.
        
        :param sliver_expires_on: expiration time following the C-Lab format 'YYY-MM-DD'
        :type string
        
        :returns datetime object with the expiration date
        :type datetime
        '''
        year, month, day = sliver_expires_on.split('-')
        dt=datetime.datetime(int(year), int(month), int(day), 00, 00, 00)
        return dt
    
    
    def clab_node_is_geni_available(self, current_state):
        '''
        Function to check if a C-Lab node is in a GENI avaialable state
        
        :param current_state: C-Lab specific current state of a Node
        :type string
        
        :returns boolean indicating if the node is currently GENI availabe
        :rtype boolean
        '''
        if current_state == 'production': return 'true'
        else: return 'false'
                
        
    def clab_state_to_geni_state(self, clab_state, allocation=False, operational=False):
        '''
        Function to translate the clab-specific states to the standard geni states.
        It includes allocation and operational states. Use boolean arguments to select
        if getting allocation or operational state. Specify one of both mandatory
        
        :param clab_state: C-Lab specific state of Node/Slice/Sliver
        :type string
        
        :param allocation: boolean indicating that allocation state is got <optional>
        :type boolean
        
        :param operational: boolean indicating that operational state is got <optional>
        :type boolean
        
        :returns GENI operational or allocation state
        :rtype string
        '''
        # NODE STATES 
        if clab_state in ['debug','safe','failure', 'offline', 'crashed']:
            # debug: the nodes has incomplete/invalid configuration
            # safe: complete/valid configuration but not available for hosting slivers
            # failure: node experimenting hw/sfw problems, not available for slivers
            return 'geni_unavailable'
        elif clab_state == 'production':
            # production: node running and available for slivers
            return 'geni_available'
        
        # SLICE/SLIVER STATES
        # Distinguish between Allocation state and Operational state
    
        # NORMAL STATES
        elif clab_state in ['register', 'registered']:
            # register(ed): slice/sliver descriptions correct and  known by the server
            if allocation: return 'geni_allocated'
            elif operational: return 'geni_notready'
            
        elif clab_state in ['deploy', 'deployed']:
            # deploy(ed): slice/slivers have requested resources allocated and data installed.
            if allocation: return 'geni_provisioned'
            elif operational: return 'geni_notready'
            
        elif clab_state in ['start', 'started']:
            # start(ed): slice/slivers are to have their components started
            if allocation: return 'geni_provisioned'
            elif operational: return 'geni_ready'
            
        elif clab_state in ['unknown', 'nodata']:
            if allocation: return 'geni_unallocated'
            elif operational: return 'geni_pending_allocation'
        
        #TRANSITORY STATES
        elif clab_state in ['allocating', '(allocating)', '(allocate)']:
            # Transitory state that runs the allocate action
            if allocation: return 'geni_unallocated'
            elif operational: return 'geni_pending_allocation'
            
        elif clab_state in ['deploying', '(deploying)']:
            # Transitory state that runs the deploy action
            if allocation: return 'geni_allocated'
            elif operational: return 'geni_notready'
            
        elif clab_state in ['starting', '(starting)']:
            # Transitory state that runs the start action
            if allocation: return 'geni_provisioned'
            elif operational: return 'geni_configuring'
        
        # FAILURE STATES
        elif clab_state =='fail_alloc':
            # Transitory state that runs the allocate action
            if allocation: return 'geni_unallocated'
            elif operational: return 'geni_failed'
            
        elif clab_state in 'fail_deploy':
            # Transitory state that runs the deploy action
            if allocation: return 'geni_allocated'
            elif operational: return 'geni_failed'
            
        elif clab_state in 'fail_start':
            # Transitory state that runs the start action
            if allocation: return 'geni_provisioned'
            elif operational: return 'geni_failed'
 
    
    #def get_slivers_by_geni_state(self, state=None):
        #'''
        #???
        #'''
        #pass
    
        
    def get_nodes_by_geni_state(self, state=None):
        '''
        Function to get the Nodes from the controller. It supports the option to get only the nodes 
        that are in geni_available state. (production state in CLab)
        
        :param state: 'available' to specify that geni_available nodes will be got <optional>
        :type string
        
        :returns list of C-Lab dictionaries decscribing the nodes
        :rtype list of dict
        '''
        nodes = self.driver.testbed_shell.get_nodes()
        if state and state=='available':
            nodes = [node for node in nodes if self.driver.testbed_shell.get_node_current_state(node=node)=='production']
        return nodes
        
            
    def get_slices_by_geni_state(self, state=None):
        '''
        Function to get the Slices from the controller. It supports the option to get only the slices 
        that are in geni_available state. (deployed, started current state in CLab)
        
        :param state: 'available' to specify that geni_available slices will be got <optional>
        :type string
        
        :returns list of C-Lab dictionaries decscribing the slices
        :rtype list of dict
        '''
        slices = self.driver.testbed_shell.get_slices()
        if state and state=='available':
            slices = [slice for slice in slices if slice['set_state'] in ['deploy','start']]
        return slices
    
    
            
        
    ########################################
    # RSPEC related and translation methods
    ########################################
    
    def clab_node_to_rspec_node(self, node, options={}):
        '''
        Translate the CLab-specific node dictionary to the standard Rspec format.
        The Rspec format used is v3 and it is augmented with specific fields from CLab.
        
        :param node: C-Lab specific Node dict OR uri of node 
        :type dict OR string
        
        :param options: various options
        :type dict
        
        :returns list of dictionaries containing the RSpec of the nodes
        :rtype list
        '''    
        # If the argument is the node uri, obtain node dict
        if isinstance(node, str):
            node = self.driver.testbed_shell.get_node_by(node_uri=node)
            
        #rspec_node = ClabNode()
        rspec_node = NodeElement()
        
        # RSpec standard fields (Advertisement RSpec)
        rspec_node['client_id'] = node['name'] # 'MyNode'
        rspec_node['component_id'] = hostname_to_urn(self.AUTHORITY, node['name']) # 'urn:publicid:IDN+confine:clab+node+MyNode'
        rspec_node['component_name'] = node['name'] # pc160  
        rspec_node['component_manager_id'] = hrn_to_urn(self.AUTHORITY, 'authority+cm') # urn:publicid:IDN+confine:clab+authority+cm
        rspec_node['authority_id'] = hrn_to_urn(self.AUTHORITY, 'authority+sa') #urn:publicid:IDN+confine:clab+authority+sa
        rspec_node['exclusive'] = 'false'
        rspec_node['available'] = self.clab_node_is_geni_available(self.driver.testbed_shell.get_node_current_state(node=node))
        rspec_node['boot_state'] = self.clab_state_to_geni_state(self.driver.testbed_shell.get_node_current_state(node=node))
        rspec_node['hardware_types'] = [HardwareType({'name': node['arch']})]
        
        # Add INTERFACES
        rspec_node['interfaces'] = self.clab_node_interfaces_to_rspec_interfaces(node)
        
        # Add SLIVERS
        rspec_node['slivers'] = self.clab_slivers_to_rspec_slivers(node)
        
        # Rspec CLab-specific fields
        # 'uri','id','name','description','arch','boot_sn','set_state','group','direct_ifaces','properties','cert','slivers',
        #            'local_iface','sliver_pub_ipv6','sliver_pub_ipv4','sliver_pub_ipv4_range','mgmt_net','sliver_mac_prefix','priv_ipv4_prefix'
        # 'current_state'
        #rspec_node['uri'] = node['uri']
        #rspec_node['id'] = node['id']
        #rspec_node['name'] = node['name']
        #rspec_node['description'] = node['description']
        #rspec_node['arch'] = node['arch']
        #rspec_node['boot_sn'] = node['boot_sn']
        #rspec_node['set_state'] = node['set_state']
        #rspec_node['current_state'] = self.driver.testbed_shell.get_node_current_state(node=node)
        #rspec_node['group'] = node['group']
        #rspec_node['direct_ifaces'] = node['direct_ifaces']
        #rspec_node['properties'] = node['properties']
        #rspec_node['cert'] = node['cert']
        #rspec_node['slivers'] = node['slivers']
        #rspec_node['local_iface'] = node['local_iface']
        #rspec_node['sliver_pub_ipv6'] = node['sliver_pub_ipv6']
        #rspec_node['sliver_pub_ipv4'] = node['sliver_pub_ipv4']
        #rspec_node['sliver_pub_ipv4_range'] = node['sliver_pub_ipv4_range']
        #rspec_node['mgmt_net'] = node['mgmt_net']
        #rspec_node['sliver_mac_prefix'] = node['sliver_mac_prefix']
        #rspec_node['priv_ipv4_prefix'] = node['priv_ipv4_prefix']
            
        return rspec_node
    
    
    
    def clab_node_interfaces_to_rspec_interfaces(self, node, options={}):
        '''
        Translate a list of CLab-specific interfaces dictionaries of a Node 
        to a list of standard Rspec interfaces.
        
        :param node: C-Lab specific dict of a node
        :type dict
        
        :param options: various options
        :type dict
        
        :returns list of dictionaries containing the RSpec of the node interfaces
        :rtype list
        ''' 
        rspec_interfaces = []
        local_iface = node['local_iface']
        direct_ifaces = node['direct_ifaces']
        
        if local_iface:
            client_id = '%s:%s'%(node['name'], local_iface)
            rspec_local_iface = dict([('interface_id', local_iface), ('node_id', node['id']), 
                                      ('role', 'local_iface'), ('client_id', client_id)])
            rspec_interfaces.append(rspec_local_iface)
        if direct_ifaces:
            for direct_iface in direct_ifaces:
                client_id = '%s:%s'%(node['name'], direct_iface)
                rspec_direct_iface = dict([('interface_id', direct_iface), ('node_id', node['id']), 
                                          ('role', 'direct_iface'), ('client_id', client_id)])
                rspec_interfaces.append(rspec_direct_iface)
                    
        return rspec_interfaces
    
    
    def clab_sliver_interfaces_to_rspec_interfaces(self, sliver, options={}):
        '''
        Translate a list of CLab-specific interfaces dictionaries of a Sliver 
        to a list of standard Rspec interfaces.
        
        :param sliver: C-Lab specific dictionary of Sliver
        :type dict
        
        :param options: various options
        :type dict
         
        :returns list of dictionaries containing the RSpec of the sliver interfaces
        :rtype list
        ''' 
        rspec_interfaces = []
        for interface in sliver['interfaces']:
            client_id = '%s:%s'%(sliver['id'],interface['name'])
            rspec_iface = dict([('interface_id', interface['nr']), ('role', interface['type']), ('client_id', client_id)])
            rspec_interfaces.append(rspec_iface)
        return rspec_interfaces
    
    
    def clab_slivers_to_rspec_slivers(self, node, options={}):
        '''
        Translate a list of CLab-specific slivers dictionaries of a Node 
        to a list of standard Rspec slivers.
        
        :param node: C-Lab specific dictionary of Node
        :type dict
        
        :param options: various options
        :type dict
         
        :returns list of dictionaries containing the RSpec of the slivers 
        :rtype list
        '''
        rspec_slivers = []
        slivers = node['slivers']
        for clab_sliver in slivers:
            sliver = self.driver.testbed_shell.get_sliver_by(sliver_uri=clab_sliver['uri'])
            disk_image = self.clab_template_to_rspec_disk_image(sliver)
            rspec_sliver = dict([('sliver_id', sliver['id']), ('client_id', sliver['id']), 
                                ('name', sliver['id']), ('type', 'RD_Sliver'), ('disk_image', disk_image)])
            rspec_slivers.append(rspec_sliver)
        return rspec_slivers  
        
    
    def clab_template_to_rspec_disk_image(self, sliver):
        '''
        Translate a CLab-specific template dictionary to 
        standard RSpec disk_image dict.

        :param node: C-Lab specific dictionary of Sliver
        :type dict
         
        :returns dictionary containing the Rspec specific disk image 
        :rtype dict
        '''  
        template = sliver ['template']
        if not template: 
            # Get template from the slice
            template_uri = self.driver.testbed_shell.get_slice_by(slice_uri=sliver['slice']['uri'])['template']['uri']
            template = self.driver.testbed_shell.get_by_uri(template_uri)
        template_rspec = dict([('name', template['name']), ('os', template['type']), ('description', template['description']) ])
        return template_rspec                        
        
    
    
    
    
    
    
    
            

    
   
    
       



