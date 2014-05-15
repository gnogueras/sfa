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
from sfa.clab.clab_xrn import slicename_to_urn, hostname_to_hrn, ClabXrn, type_of_urn, get_slice_by_sliver_urn, urn_to_slicename
from sfa.clab.clab_logging import clab_logger


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
        self.config = api.config
        self.testbed_shell = ClabShell (self.config)
        self.cache=None
        
        # Debug print
        print "SFA_INTERFACE_HRN: %s"%(self.config.SFA_INTERFACE_HRN)
        print "SFA_REGISTRY_ROOT_AUTH: %s"%(self.config.SFA_REGISTRY_ROOT_AUTH)
        print "SFA_GENERIC_FLAVOUR: %s"%(self.config.SFA_GENERIC_FLAVOUR)
        print "SFA_CLAB_USER: %s"%(self.config.SFA_CLAB_USER)
        print "SFA_CLAB_PASSWORD: %s"%(self.config.SFA_CLAB_PASSWORD)
        print "SFA_CLAB_GROUP: %s"%(self.config.SFA_CLAB_GROUP)
        print "SFA_CLAB_URL: %s"%(self.config.SFA_CLAB_URL)
        print "SFA_CLAB_AUTO_SLICE_CREATION: %s"%(self.config.SFA_CLAB_AUTO_SLICE_CREATION)
        print "SFA_CLAB_AUTO_NODE_CREATION: %s"%(self.config.SFA_CLAB_AUTO_NODE_CREATION)
        print "SFA_CLAB_DEFAULT_TEMPLATE: %s"%(self.config.SFA_CLAB_DEFAULT_TEMPLATE)
        print "SFA_CLAB_TEMP_DIR_EXP_DATA: %s"%(self.config.SFA_CLAB_TEMP_DIR_EXP_DATA)
               
        # Get it from CONFIG
        self.AUTHORITY = ".".join([self.config.SFA_INTERFACE_HRN,self.config.SFA_GENERIC_FLAVOUR])
        self.TESTBEDNAME = self.config.SFA_GENERIC_FLAVOUR
        self.AUTOMATIC_SLICE_CREATION = self.config.SFA_CLAB_AUTO_SLICE_CREATION
        self.AUTOMATIC_NODE_CREATION = self.config.SFA_CLAB_AUTO_NODE_CREATION
        self.EXP_DATA_DIR = self.config.SFA_CLAB_TEMP_DIR_EXP_DATA
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
        # build list of cred object hrns, NOT NEEDED NOW
        slice_cred_names = []
        for cred in creds:
            slice_cred_hrn = Credential(cred=cred).get_gid_object().get_hrn()
            slice_cred_names.append(ClabXrn(xrn=slice_cred_hrn).get_slicename())

        # build list of urns of objects on which the credentials give rights
        slice_cred_urns = []
        for cred in creds:
            slice_cred_urn = Credential(cred=cred).get_gid_object().get_urn()
            slice_cred_urns.append(slice_cred_urn)
        
        # Get the slice names of all the slices included in the urn
        slice_names = []
        slice_urns = []
        for urn in urns:
            if type_of_urn(urn)=='sliver':
                # URN of a sliver. Get the slice where the sliver is contained
                slice = get_slice_by_sliver_urn(self, urn)
                slice_names.append(slice['name'])
                slice_urns.append(slicename_to_urn(slice['name']))
            elif type_of_urn(urn)=='slice':
                # URN of a slice
                slice_names.append(urn_to_slicename(urn))
                slice_urns.append(urn)
        
        if not slice_urns:
             raise Forbidden("sliver urn not provided")

        # make sure we have a credential for every specified sliver ierd
        for slice_urn in slice_urns:
            if slice_urn not in slice_cred_urns:
                msg = "Valid credential not found for target: %s" % slice_urn
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
        clab_logger.debug("%s:%s - Clab_Registry: register %s \n SFA_record details: %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, hrn, sfa_record))
        registry = ClabRegistry(self)
        return registry.register(sfa_record, hrn, pub_key)
    
        
    def remove (self, sfa_record):
        '''
        SFA Registry API Remove
        '''
        clab_logger.debug("%s:%s - Clab_Registry: remove %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, sfa_record))
        registry = ClabRegistry(self)
        return registry.remove(sfa_record)
    
    
    def update (self, old_sfa_record, new_sfa_record, hrn, new_key=None):
        '''
        SFA Registry API Update
        '''
        clab_logger.debug("%s:%s - Clab_Registry: update %s \n OLD SFA_record details: %s \n NEW SFA_record details: %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, hrn, old_sfa_record, new_sfa_record))
        registry = ClabRegistry(self)
        return registry.update(old_sfa_record, new_sfa_record, hrn, new_key)

    
    def update_relation (self, subject_type, target_type, relation_name, subject_id, target_ids):
        '''
        SFA Registry API Update relation
        '''
        clab_logger.debug("%s:%s - Clab_Registry: update relation \n Details: %s (%s) is now '%s' for %s (%s) "%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, subject_id, subject_type, relation_name, target_ids, target_type))
        registry = ClabRegistry(self)
        return registry.update_relation(subject_type, target_type, relation_name, subject_id, target_ids)
                                                                            
        
    
    #########################################
    #####      aggregate oriented       #####
    #########################################
    
    def testbed_name(self):
        """
        Method to return the name of the testbed
        """ 
        return "C-Lab"
    
    def aggregate_version(self):
        """
        GENI AM API v3 GetVersion
        """
        clab_logger.debug("%s:%s - Clab_Aggregate: get version"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP))
        aggregate = ClabAggregate(self)
        version = aggregate.get_version()
        
        return {
            'testbed': 'C-Lab',
            'geni_request_rspec_versions': version['value']['geni_request_rspec_versions'],
            'geni_ad_rspec_versions': version['value']['geni_ad_rspec_versions']
            }
    
    
    def list_resources(self, version, options={}):
        '''
        GENI AM API v3 ListResources
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: list resources"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP))
        aggregate = ClabAggregate(self)
        return aggregate.list_resources(options=options)
    
    
    def describe(self, urns, version, options={}):
        '''
        GENI AM API v3 Describe
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: Describe %s "%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, urns))
        aggregate = ClabAggregate(self)
        return aggregate.describe(urns, options=options)    
    
    
    def allocate(self, slice_urn, rspec_string, expiration, options={}):
        '''
        GENI AM API v3 Allocate
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: allocate %s \n RSpec details: %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, slice_urn, rspec_string))
        aggregate = ClabAggregate(self)
        return aggregate.allocate(slice_urn, rspec_string, expiration, options=options)
    
    
    def renew(self, urns, expiration_time, options={}):
        '''
        GENI AM API v3 Renew
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: renew %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, urns))
        aggregate = ClabAggregate(self)
        return aggregate.renew(urns, expiration_time, options=options)
    
    
    def provision(self, urns, options={}):
        '''
        GENI AM API v3 Provision
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: provision %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, urns))
        aggregate = ClabAggregate(self)
        return aggregate.provision(urns, options=options)
    
    
    def status (self, urns, options={}):
        '''
        GENI AM API v3 Status
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: status %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, urns))
        aggregate = ClabAggregate(self)
        return aggregate.status(urns, options=options)


    def perform_operational_action(self, urns, action, options={}):
        '''
        GENI AM API v3 PerformOperationalAction
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: perform operational action [%s] on %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP,action,urns))
        aggregate = ClabAggregate(self)
        return aggregate.perform_operational_action(urns, action, options=options)
        
     
    def delete(self, urns, options={}):
        '''
        GENI AM API v3 Delete
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: delete %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, urns))
        aggregate = ClabAggregate(self)
        return aggregate.delete(urns, options=options)
   
   
    def shutdown(self, slice_urn, options={}):
        '''
        GENI AM API v3 Shutdown
        '''
        clab_logger.debug("%s:%s - Clab_Aggregate: shutdown %s"%(self.config.SFA_CLAB_USER, self.config.SFA_CLAB_GROUP, slice_urn))
        aggregate = ClabAggregate(self)
        return aggregate.shutdown(slice_urn, options=options)
    
    
    
        




