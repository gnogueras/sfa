'''
Created on Mar 5, 2014

@author: gerard
'''
import os

from sfa.clab.clab_shell import ClabShell    
from sfa.clab.clab_xrn import hostname_to_hrn, slicename_to_hrn
from sfa.storage.alchemy import global_dbsession
from sfa.storage.model import RegRecord, RegAuthority, RegSlice, RegNode, RegUser, RegKey
from sfa.trust.certificate import convert_public_key, Keypair
from sfa.trust.gid import create_uuid    
from sfa.util.config import Config
from sfa.util.xrn import Xrn, get_leaf, get_authority, hrn_to_urn


# using global alchemy.session() here is fine 
# as importer is on standalone one-shot process
def _get_site_hrn(interface_hrn, site):
     hrn = ".".join([interface_hrn, site['name']])
     return hrn


class ClabImporter:
    
    def __init__ (self, auth_hierarchy, logger):
        print "Method init of ClabImporter class"
        self.auth_hierarchy = auth_hierarchy
        self.logger=logger
    
    
    def add_options (self, parser):
        # we don't have any options for now
        pass
    
    
    # Add/remember record a to a hrn-tuple keyed dictionary of records
    # to avoid duplicates in the database
    def remember_record_by_hrn (self, record):
        tuple = (record.type, record.hrn)
        if tuple in self.records_by_type_hrn:
            self.logger.warning ("CLabImporter.remember_record_by_hrn: duplicate (%s,%s)"%tuple)
            return
        self.records_by_type_hrn [ tuple ] = record

    # Add/remeber record a to a pointer-tuple keyed dictionary of records
    # to avoid duplicates in the database
    def remember_record_by_pointer (self, record):
        if record.pointer == -1:
            self.logger.warning ("CLabImporter.remember_record_by_pointer: pointer is void")
            return
        tuple = (record.type, record.pointer)
        if tuple in self.records_by_type_pointer:
            self.logger.warning ("CLabImporter.remember_record_by_pointer: duplicate (%s,%s)"%tuple)
            return
        self.records_by_type_pointer [ ( record.type, record.pointer,) ] = record

    # Generic add/remember method for records (hrn and pointer)
    def remember_record (self, record):
        self.remember_record_by_hrn (record)
        self.remember_record_by_pointer (record)
    
    # Get/locate record from the hrn-tuple keyed dictionary
    def locate_by_type_hrn (self, type, hrn):
        return self.records_by_type_hrn.get ( (type, hrn), None)
    
    # Get/locate record from the pointer-tuple keyed dictionary
    def locate_by_type_pointer (self, type, pointer):
        return self.records_by_type_pointer.get ( (type, pointer), None)


    # Run Importer method
    def run (self, options):
        config = Config ()
        interface_hrn = config.SFA_INTERFACE_HRN
        root_auth = config.SFA_REGISTRY_ROOT_AUTH
        shell = ClabShell (config)
        
        print "Running RUN method in ClabImporter class"
        
        # retrieve all existing SFA objects
        all_records = global_dbsession.query(RegRecord).all()
        
        # Dicts to avoid duplicates in SFA database
        # create dict keyed by (type,hrn) 
        self.records_by_type_hrn = dict([((record.type, record.hrn), record) for record in all_records ] )
        # create dict keyed by (type,pointer) 
        self.records_by_type_pointer = dict([((record.type, record.pointer), record) for record in all_records if record.pointer != -1])
        
        # initialize record.stale to True by default, then mark stale=False on the ones that are in use
        for record in all_records: record.stale=True
        
        # Retrieve data from the CLab testbed and create dictionaries by id
        # SITE
        site = shell.get_testbed_info()
        # USERS
        users = shell.get_users({})
        users_by_id = dict ( [ ( user['user_id'], user) for user in users ] )
        # KEYS
        # auth_tokens of the users. Dict (user_id:[keys])
        
        # NODES
        nodes = shell.get_nodes({})
        nodes_by_id = dict ( [ ( node['node_id'], node, ) for node in nodes ] )
        # SLICES
        slices = shell.get_slices({})
        slices_by_id = dict ( [ (slice['slice_id'], slice ) for slice in slices ] )
        
        # Import records to the SFA registry
        # SITE
        # USERS
        # KEYS
        # NODES
        # SLICES

