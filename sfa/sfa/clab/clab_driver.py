# -*- coding: utf-8 -*-
'''
Created on 06/02/2014

@author: gerard
'''

from sfa.managers.driver import Driver
from sfa.rspecs.rspec import RSpec
from sfa.rspecs.version_manager import VersionManager
from sfa.storage.model import RegRecord
from sfa.util.cache import Cache
from sfa.util.defaultdict import defaultdict
from sfa.util.faults import MissingSfaInfo, UnknownSfaType, \
    RecordNotFound, SfaNotImplemented, SliverDoesNotExist
from sfa.util.sfalogging import logger
from sfa.util.sfatime import utcparse, datetime_to_string, datetime_to_epoch
from sfa.util.xrn import Xrn, hrn_to_urn, get_leaf, urn_to_hrn

from clab.clab_aggregate import ClabAggregate
from clab.clab_registry import ClabRegistry
from clab.clab_shell import ClabShell
import clab.clab_xrn
from clab.clab_xrn import slicename_to_hrn, hostname_to_hrn

#
# ClabShell is just an xmlrpc serverproxy where methods
# can be sent as-is; it takes care of authentication
# from the global config
# 
class ClabDriver (Driver):

    # the cache instance is a class member so it survives across incoming requests
    cache = None

    def __init__ (self, api):
        #Driver.__init__ (self, api)
        config = api.config
        self.testbed_shell = ClabShell (config)
        self.cache=None
        
        # Get it from CONFIG
        self.AUTHORITY = 'confine.clab'
        self.TESTBEDNAME = 'C-Lab'
        self.AUTOMATIC_SLICE_CREATION = True
        self.AUTOMATIC_NODE_CREATION = False
                
# un-comment below lines to enable caching
#        if config.SFA_AGGREGATE_CACHING:
#            if ClabDriver.cache is None:
#                ClabDriver.cache = Cache()
#            self.cache = ClabDriver.cache



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
            'testbed': self.TESTBEDNAME,
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
    
    
    
        




