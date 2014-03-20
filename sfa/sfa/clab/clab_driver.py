# -*- coding: utf-8 -*-
'''
Created on 06/02/2014

@author: gerard
'''

from sfa.managers.driver import Driver
from sfa.rspecs.rspec import RSpec
from sfa.rspecs.version_manager import VersionManager
from sfa.util.cache import Cache
from sfa.util.defaultdict import defaultdict
from sfa.util.faults import MissingSfaInfo, UnknownSfaType, \
    RecordNotFound, SfaNotImplemented, SliverDoesNotExist, Forbidden
from sfa.util.sfalogging import logger
from sfa.util.sfatime import utcparse, datetime_to_string, datetime_to_epoch
from sfa.util.xrn import Xrn, hrn_to_urn, get_leaf, urn_to_hrn
from sfa.storage.model import RegRecord, SliverAllocation
from sfa.trust.credential import Credential

from sfa.clab.clab_aggregate import ClabAggregate
from sfa.clab.clab_registry import ClabRegistry
from sfa.clab.clab_shell import ClabShell
from sfa.clab.clab_xrn import slicename_to_hrn, hostname_to_hrn, ClabXrn, type_of_urn, get_slice_by_sliver_urn, urn_to_slicename

#
# ClabShell is just an xmlrpc serverproxy where methods
# can be sent as-is; it takes care of authentication
# from the global config
# 
class ClabDriver (Driver):

    # the cache instance is a class member so it survives across incoming requests
    cache = None

    def __init__ (self, api):
        Driver.__init__ (self, api)
        config = api.config
        self.testbed_shell = ClabShell (config)
        self.cache=None
        
        # Debug print
        print "SFA_INTERFACE_HRN: %s"%(config.SFA_INTERFACE_HRN)
        print "SFA_REGISTRY_ROOT_AUTH: %s"%(config.SFA_REGISTRY_ROOT_AUTH)
        print "SFA_GENERIC_FLAVOUR: %s"%(config.SFA_GENERIC_FLAVOUR)
        print "SFA_CLAB_USER: %s"%(config.SFA_CLAB_USER)
        print "SFA_CLAB_PASSWORD: %s"%(config.SFA_CLAB_PASSWORD)
        print "SFA_CLAB_GROUP: %s"%(config.SFA_CLAB_GROUP)
        print "SFA_CLAB_AUTO_SLICE_CREATION: %s"%(config.SFA_CLAB_AUTO_SLICE_CREATION)
        print "SFA_CLAB_AUTO_NODE_CREATION: %s"%(config.SFA_CLAB_AUTO_NODE_CREATION)
        print "SFA_CLAB_URL: %s"%(config.SFA_CLAB_URL)
        
        
        # Get it from CONFIG
        self.AUTHORITY = ".".join([config.SFA_INTERFACE_HRN,config.SFA_GENERIC_FLAVOUR])
        self.TESTBEDNAME = config.SFA_GENERIC_FLAVOUR
        self.AUTOMATIC_SLICE_CREATION = config.SFA_CLAB_AUTO_SLICE_CREATION
        self.AUTOMATIC_NODE_CREATION = config.SFA_CLAB_AUTO_NODE_CREATION
        #self.AUTHORITY = 'confine.clab'
        #self.TESTBEDNAME = 'C-Lab'
        #self.AUTOMATIC_SLICE_CREATION = True
        #self.AUTOMATIC_NODE_CREATION = False
                
# un-comment below lines to enable caching
#        if config.SFA_AGGREGATE_CACHING:
#            if ClabDriver.cache is None:
#                ClabDriver.cache = Cache()
#            self.cache = ClabDriver.cache



    def check_sliver_credentials(self, creds, urns):
        '''
        Function used in some methods from /sfa/sfa/methods.
        It checks that there is a valid credential for each of the slices referred in the urns argument.
        The slices can be referred by their urn or by the urn of a sliver contained in it.
        
        :param creds: list of available slice credentials
        :type list (of Credential objects)
        
        :param urns: list of urns that refer to slices (directly or through a sliver)
        :type list (of strings)
        
        :return nothing
        :rtype void
        '''
        # build list of cred object hrns
        slice_cred_names = []
        for cred in creds:
            slice_cred_hrn = Credential(cred=cred).get_gid_object().get_hrn()
            slice_cred_names.append(ClabXrn(xrn=slice_cred_hrn).get_slicename())

        # Get the slice names of all the slices included in the urn
        slice_names = []
        for urn in urns:
            if type_of_urn(urn)=='sliver':
                # URN of a sliver. Get the slice where the sliver is contained
                slice = get_slice_by_sliver_urn(self, urn)
                slice_names.append(slice['name'])
            elif type_of_urn(urn)=='slice':
                # URN of a slice
                slice_names.append(urn_to_slicename(urn))
        
        if not slice_names:
             raise Forbidden("sliver urn not provided")

        # make sure we have a credential for every specified sliver ierd
        for sliver_name in slice_names:
            if sliver_name not in slice_cred_names:
                msg = "Valid credential not found for target: %s" % sliver_name
                raise Forbidden(msg)
 



    ########################################
    #####      registry oriented       #####
    ########################################

    def augment_records_with_testbed_info (self, sfa_records):
        '''
        SFA Registry API 
        '''
        registry = ClabRegistry(self)
        return registry.augment_records_with_testbed_info(sfa_records)
    
    
    def register (self, sfa_record, hrn, pub_key=None):
        '''
        SFA Registry API Register
        '''
        registry = ClabRegistry(self)
        return registry.register(sfa_record, hrn, pub_key)
    
        
    def remove (self, sfa_record):
        '''
        SFA Registry API Remove
        '''
        registry = ClabRegistry(self)
        return registry.remove(sfa_record)
    
    
    def update (self, old_sfa_record, new_sfa_record, hrn, new_key=None):
        '''
        SFA Registry API Update
        '''
        registry = ClabRegistry(self)
        return registry.update(old_sfa_record, new_sfa_record, hrn, new_key)

    
    def update_relation (self, subject_type, target_type, relation_name, subject_id, target_ids):
        '''
        SFA Registry API Update relation
        '''
        registry = ClabRegistry(self)
        return registry.update_relation(subject_type, target_type, relation_name, subject_id, target_ids)
                                                                            
        
    
    #########################################
    #####      aggregate oriented       #####
    #########################################
    
    def aggregate_version(self):
        """
        GENI AM API v3 GetVersion
        """
        aggregate = ClabAggregate(self)
        version = aggregate.get_version()
        
        return {
            'testbed': 'C-Lab',
            'geni_request_rspec_versions': version['value']['geni_request_rspec_versions'],
            'geni_ad_rspec_versions': version['value']['geni_ad_rspec_versions']
            }
    
    
    def list_resources(self, credentials, options={}):
        '''
        GENI AM API v3 ListResources
        '''
        aggregate = ClabAggregate(self)
        return aggregate.list_resources(credentials, options)
    
    
    def describe(self, urns, credentials, options={}):
        '''
        GENI AM API v3 Describe
        '''
        print "CLAB_DRIVER DESCRIBE METHOD"
        aggregate = ClabAggregate(self)
        return aggregate.describe(urns, credentials, options)    
    
    
    def allocate(self, slice_urn, credentials, rspec_string, options={}):
        '''
        GENI AM API v3 Allocate
        '''
        aggregate = ClabAggregate(self)
        return aggregate.allocate(slice_urn, credentials, rspec_string, options)
    
    
    def renew(self, urns, credentials, expiration_time, options={}):
        '''
        GENI AM API v3 Renew
        '''
        aggregate = ClabAggregate(self)
        return aggregate.renew(urns, credentials, expiration_time, options)
    
    
    def provision(self, urns, credentials, options={}):
        '''
        GENI AM API v3 Provision
        '''
        aggregate = ClabAggregate(self)
        return aggregate.provision(urns, credentials, options)
    
    
    def status (self, urns, credentials, options={}):
        '''
        GENI AM API v3 Status
        '''
        aggregate = ClabAggregate(self)
        return aggregate.status(urns, credentials, options)


    def perform_operational_action(self, urns, credentials, action, options={}):
        '''
        GENI AM API v3 PerformOperationalAction
        '''
        aggregate = ClabAggregate(self)
        return aggregate.perform_operational_action(urns, credentials, action, options)
        
     
    def delete(self, urns, credentials, options):
        '''
        GENI AM API v3 Delete
        '''
        aggregate = ClabAggregate(self)
        return aggregate.delete(urns, credentials, options)
   
   
    def shutdown(self, slice_urn, credentials, options={}):
        '''
        GENI AM API v3 Shutdown
        '''
        aggregate = ClabAggregate(self)
        return aggregate.shutdown(slice_urn, credentials, options)
    
    
    
        




