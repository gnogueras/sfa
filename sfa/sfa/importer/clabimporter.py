'''
Created on Mar 5, 2014

@author: gerard
'''
import os

from sfa.clab.clab_shell import ClabShell    
from sfa.clab.clab_xrn import hostname_to_hrn, slicename_to_hrn, username_to_hrn
from sfa.storage.alchemy import global_dbsession
from sfa.storage.model import RegRecord, RegAuthority, RegSlice, RegNode, RegUser, RegKey
from sfa.trust.certificate import convert_public_key, Keypair
from sfa.trust.gid import create_uuid    
from sfa.util.config import Config
from sfa.util.xrn import get_authority, hrn_to_urn


# using global alchemy.session() here is fine 
# as importer is on standalone one-shot process
def _get_site_hrn(interface_hrn, site):
    '''
    Auxiliary method to get the site hrn from the interface hrn and the authority site.
    
    :param interface_hrn: hrn of the interfaces, from the configuration of SFA
    :type string
    
    :param site: information from the site. In our case, about the testbed.
    :type dict
    
    :returns hrn of the authority site
    :rtype string 
    '''
    hrn = ".".join([interface_hrn, site['name']])
    return hrn


class ClabImporter:
    '''
    Importer class for the CLab testbed.
    This class imports the records/information from the database of testbed
    to the generic SFA Registry, so both databases can sync from the begining.
    Such import operation involves translation from testbed-specific records
    to SFA standard records.
    '''
    
    def __init__ (self, auth_hierarchy, logger):
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
                
        # retrieve all existing SFA objects
        all_records = global_dbsession.query(RegRecord).all()
        
        # Delete all default records
        #for record in all_records:
        #    global_dbsession.delete(record)
        #    global_dbsession.commit()
        #all_records = global_dbsession.query(RegRecord).all()
        
        # Dicts to avoid duplicates in SFA database
        # create dict keyed by (type,hrn) 
        self.records_by_type_hrn = dict([((record.type, record.hrn), record) for record in all_records ] )
        # create dict keyed by (type,pointer) 
        self.records_by_type_pointer = dict([((record.type, record.pointer), record) for record in all_records if record.pointer != -1])
        
        # initialize record.stale to True by default, then mark stale=False on the ones that are in use
        for record in all_records: 
            record.stale=True
        
        # Retrieve data from the CLab testbed and create dictionaries by id
        # SITE
        sites = [shell.get_testbed_info()]
        
        # USERS
        users = shell.get_users({})
        
        #users_by_id = dict ( [ ( user['id'], user) for user in users ] )
        # KEYS
        # auth_tokens of the users. Dict (user_id:[keys])
        
        # NODES
        nodes = shell.get_nodes({})
        
        # SLICES
        slices = shell.get_slices({})
        
        
        # Import records to the SFA registry
        # SITE
        for site in sites:
            # Get hrn of the site (authority)
            site_hrn = _get_site_hrn(interface_hrn, site)
            # Try to locate the site_hrn in the SFA records
            site_record=self.locate_by_type_hrn ('authority', site_hrn)
            
            if not site_record:
                # Create/Import record for the site authority
                try:
                    urn = hrn_to_urn(site_hrn, 'authority')
                    if not self.auth_hierarchy.auth_exists(urn):
                        self.auth_hierarchy.create_auth(urn)
                    auth_info = self.auth_hierarchy.get_auth_info(urn)
                    # Create record for the site authority and add it to the Registry
                    site_record = RegAuthority(hrn=site_hrn, gid=auth_info.get_gid_object(),
                                               pointer= -1,
                                               authority=get_authority(site_hrn))
                    site_record.just_created()
                    global_dbsession.add(site_record)
                    global_dbsession.commit()
                    self.logger.info("CLabImporter: imported authority (site) : %s" % site_hrn) 
                    self.remember_record (site_record)
                except:
                    # if the site import fails then there is no point in trying to import the
                    # site's child records (node, slices, persons), so skip them.
                    self.logger.log_exc("CLabImporter: failed to import site. Skipping child records") 
                    continue 
            else:
                # Authority record already in the SFA registry. Update?
                pass
            
            # Fresh record in SFA Registry
            site_record.stale=False
            
            # DEBUG
            #print '*********** ALL RECORDS ***********'
            #all_records = global_dbsession.query(RegRecord).all()
            #for record in all_records: 
            #    print record
            
             
            # For the current site authority, import child entities/records
            
            # NODES
            for node in nodes:
                # Obtain parameters of the node: site_auth, site_name and hrn of the node
                site_auth = get_authority(site_hrn)
                site_name = site['name']
                node_hrn =  hostname_to_hrn(site_hrn, node['name'])
                # Reduce hrn up to 64 characters
                if len(node_hrn) > 64: node_hrn = node_hrn[:64]
                
                # Try to locate the node_hrn in the SFA records
                node_record = self.locate_by_type_hrn ('node', node_hrn )
                if not node_record:
                    # Create/Import record for the node
                    try:
                        # Create a keypair for the node
                        pkey = Keypair(create=True)
                        # Obtain parameters 
                        urn = hrn_to_urn(node_hrn, 'node')
                        node_gid = self.auth_hierarchy.create_gid(urn, create_uuid(), pkey)
                        # Create record for the node and add it to the Registry
                        node_record = RegNode (hrn=node_hrn, gid=node_gid, 
                                               pointer =node['id'],
                                               authority=get_authority(node_hrn))
                        node_record.just_created()
                        global_dbsession.add(node_record)
                        global_dbsession.commit()
                        self.logger.info("CLabImporter: imported node: %s" %node_hrn)  
                        self.remember_record (node_record)
                    except:
                        self.logger.log_exc("CLabImporter: failed to import node") 
                else:
                    # Node record already in the SFA registry. Update?
                    pass
                
                # Fresh record in SFA Registry
                node_record.stale=False
                # DEBUG
                #print '*********** ALL RECORDS ***********'
                #all_records = global_dbsession.query(RegRecord).all()
                #for record in all_records: 
                #    print record
                
    
            # USERS
            for user in users:
                # dummyimporter uses email... but Clab can use user['name']
                user_hrn = username_to_hrn (site_hrn, user['name'])
                # Reduce hrn up to 64 characters
                if len(user_hrn) > 64: user_hrn = user_hrn[:64]
                user_urn = hrn_to_urn(user_hrn, 'user')
                
                # Try to locate the user_hrn in the SFA records
                user_record = self.locate_by_type_hrn ('user', user_hrn)


                # Auxiliary function to get the keypair of the user from the testbed database
                # If multiple keys, randomly pick the first key in the set
                # If no keys, generate a new keypair for the user's gird
                def init_user_key (user):
                    pubkey = None
                    pkey = None
                    if  user['auth_tokens']:
                        # randomly pick first key in set
                        for key in user['auth_tokens']:
                            pubkey = key
                            try:
                                pkey = convert_public_key(pubkey)
                                break
                            except:
                                continue
                        if not pkey:
                            self.logger.warn('CLabImporter: unable to convert public key for %s' % user_hrn)
                            pkey = Keypair(create=True)
                    else:
                        # the user has no keys. Creating a random keypair for the user's gid
                        self.logger.warn("CLabImporter: user %s does not have a CLab public key"%user_hrn)
                        pkey = Keypair(create=True)
                    return (pubkey, pkey)
                ###########################
                
                try:
                    if not user_record:
                        # Create/Import record for the user
                        # Create a keypair for the node
                        (pubkey,pkey) = init_user_key (user)
                        # Obtain parameters
                        user_gid = self.auth_hierarchy.create_gid(user_urn, create_uuid(), pkey)
                        user_gid.set_email("%s@clabwrap.eu"%(user['name']))
                        # Create record for the node and add it to the Registry
                        user_record = RegUser (hrn=user_hrn, gid=user_gid, 
                                                 pointer=user['id'], 
                                                 authority=get_authority(user_hrn),
                                                 email="%s@clabwrap.eu"%(user['name']))
                        if pubkey: 
                            user_record.reg_keys=[RegKey (pubkey)]
                        else:
                            self.logger.warning("No key found for user %s"%user_hrn)
                        user_record.just_created()
                        global_dbsession.add (user_record)
                        global_dbsession.commit()
                        self.logger.info("ClabImporter: imported person: %s" % user_hrn)
                        self.remember_record ( user_record )

                    else:
                        # update the record ?
                        # if user's primary key has changed then we need to update the 
                        # users gid by forcing an update here
                        sfa_keys = user_record.reg_keys
                        def key_in_list (key,sfa_keys):
                            for reg_key in sfa_keys:
                                if reg_key.key==key: return True
                            return False
                        # is there a new key in Dummy TB ?
                        new_keys=False
                        for key in user['auth_tokens']:
                            if not key_in_list (key,sfa_keys):
                                new_keys = True
                        if new_keys:
                            (pubkey,pkey) = init_user_key (user)
                            user_gid = self.auth_hierarchy.create_gid(user_urn, create_uuid(), pkey)
                            if not pubkey:
                                user_record.reg_keys=[]
                            else:
                                user_record.reg_keys=[ RegKey (pubkey)]
                            self.logger.info("CLabImporter: updated person: %s" % user_hrn)
                    user_record.email = "%s@clabwrap.eu"%(user['name'])
                    global_dbsession.commit()
                                        
                    # Fresh record in SFA Registry
                    user_record.stale=False
                except:
                    self.logger.log_exc("CLabImporter: failed to import user %d %s"%(user['id'],user['name']))
            
            # DEBUG
                #print '*********** ALL RECORDS ***********'
                #all_records = global_dbsession.query(RegRecord).all()
                #for record in all_records: 
                #    print record         
                    
            # SLICES
            for slice in slices:
                # Obtain parameters of the node: site_auth, site_name and hrn of the slice
                slice_hrn = slicename_to_hrn(site_hrn, slice['name'])
                # Try to locate the slice_hrn in the SFA records
                slice_record = self.locate_by_type_hrn ('slice', slice_hrn)
                
                if not slice_record:
                    # Create/Import record for the slice
                    try:
                        #Create a keypair for the slice
                        pkey = Keypair(create=True)
                        # Obtain parameters
                        urn = hrn_to_urn(slice_hrn, 'slice')
                        slice_gid = self.auth_hierarchy.create_gid(urn, create_uuid(), pkey)
                        # Create record for the slice and add it to the Registry
                        slice_record = RegSlice (hrn=slice_hrn, gid=slice_gid, 
                                                 pointer=slice['id'],
                                                 authority=get_authority(slice_hrn))
                        slice_record.just_created()
                        global_dbsession.add(slice_record)
                        global_dbsession.commit()
                        self.logger.info("CLabImporter: imported slice: %s" % slice_hrn)  
                        self.remember_record ( slice_record )
                    except:
                        self.logger.log_exc("CLabImporter: failed to import slice")
                else:
                    # Slice record already in the SFA registry. Update?
                    self.logger.warning ("Slice already existing in SFA Registry")
                    pass
                
                # Get current users associated with the slice
                users_of_slice = shell.get_users_by_slice(slice)
                # record current users associated with the slice
                slice_record.reg_researchers = \
                    [ self.locate_by_type_pointer ('user',user['id']) for user in users_of_slice]
                global_dbsession.commit()
                                
                # Fresh record in SFA Registry 
                slice_record.stale=False    
                
     
        # Remove stale records. Old/non-fresh records that were in the SFA Registry
        
        # Preserve special records 
        system_hrns = [interface_hrn, root_auth, interface_hrn + '.slicemanager']
        for record in all_records: 
            if record.hrn in system_hrns: 
                record.stale=False
            if record.peer_authority:
                record.stale=False
                
        # Remove all the records that do not have its stale parameter set to False
        for record in all_records:
            try:
                stale=record.stale
            except:     
                stale=True
                self.logger.warning("stale not found with %s"%record)
            if stale:
                self.logger.info("CLabImporter: deleting stale record: %s" % record)
                global_dbsession.delete(record)
                global_dbsession.commit()
                
        # DEBUG
        print 'SFA REGISTRY - Result of Import:'
        all_records = global_dbsession.query(RegRecord).all()
        for record in all_records: 
            print record  
        
        
    def import_single_node(self, nodename):
        config = Config ()
        interface_hrn = config.SFA_INTERFACE_HRN
        root_auth = config.SFA_REGISTRY_ROOT_AUTH
        shell = ClabShell (config)
        
        self.logger.debug("Import Single node: %s"%nodename)
                
        # retrieve all existing SFA objects
        all_records = global_dbsession.query(RegRecord).all()
        
        # Dicts to avoid duplicates in SFA database
        # create dict keyed by (type,hrn) 
        self.records_by_type_hrn = dict([((record.type, record.hrn), record) for record in all_records ] )
        # create dict keyed by (type,pointer) 
        self.records_by_type_pointer = dict([((record.type, record.pointer), record) for record in all_records if record.pointer != -1])
        
        # Retrieve data from the CLab testbed and create dictionaries by id
        # SITE
        site = shell.get_testbed_info()
        
        # NODES
        node = shell.get_node_by(node_name=nodename)
        
        # Import records to the SFA registry
        # SITE
        # Get hrn of the site (authority)
        site_hrn = _get_site_hrn(interface_hrn, site)
        # Try to locate the site_hrn in the SFA records
        #site_record=self.locate_by_type_hrn ('authority', site_hrn)
                
        # NODE
        # Obtain parameters of the node: site_auth, site_name and hrn of the node
        site_auth = get_authority(site_hrn)
        site_name = site['name']
        node_hrn =  hostname_to_hrn(site_hrn, node['name'])
        # Reduce hrn up to 64 characters
        if len(node_hrn) > 64: node_hrn = node_hrn[:64]
        
        # Try to locate the node_hrn in the SFA records
        node_record = self.locate_by_type_hrn ('node', node_hrn )
        if not node_record:
            # Create/Import record for the node
            try:
                # Create a keypair for the node
                pkey = Keypair(create=True)
                # Obtain parameters 
                urn = hrn_to_urn(node_hrn, 'node')
                node_gid = self.auth_hierarchy.create_gid(urn, create_uuid(), pkey)
                # Create record for the node and add it to the Registry
                node_record = RegNode (hrn=node_hrn, gid=node_gid, 
                                       pointer =node['id'],
                                       authority=get_authority(node_hrn))
                node_record.just_created()
                global_dbsession.add(node_record)
                global_dbsession.commit()
                self.logger.info("CLabImporter: imported node: %s" %node_hrn)  
                self.remember_record (node_record)
            except:
                self.logger.log_exc("CLabImporter: failed to import node") 
        else:
            # Node record already in the SFA registry. Update?
            pass
                
    
    
    def import_single_slice(self, slicename):
        config = Config ()
        interface_hrn = config.SFA_INTERFACE_HRN
        root_auth = config.SFA_REGISTRY_ROOT_AUTH
        shell = ClabShell (config)
        
        self.logger.debug("Import Single slice: %s"%slicename)
                
        # retrieve all existing SFA objects
        all_records = global_dbsession.query(RegRecord).all()
        
        # Dicts to avoid duplicates in SFA database
        # create dict keyed by (type,hrn) 
        self.records_by_type_hrn = dict([((record.type, record.hrn), record) for record in all_records ] )
        # create dict keyed by (type,pointer) 
        self.records_by_type_pointer = dict([((record.type, record.pointer), record) for record in all_records if record.pointer != -1])
        
        # Retrieve data from the CLab testbed and create dictionaries by id
        # SITE
        site = shell.get_testbed_info()

        # SLICES
        slice = shell.get_slice_by(slice_name=slicename)
        
        # Import records to the SFA registry
        # SITE
        # Get hrn of the site (authority)
        site_hrn = _get_site_hrn(interface_hrn, site)
        # Try to locate the site_hrn in the SFA records
        #site_record=self.locate_by_type_hrn ('authority', site_hrn)
        
        # For the current site authority, import child entities/records    
        # SLICES
        # Obtain parameters of the node: site_auth, site_name and hrn of the slice
        slice_hrn = slicename_to_hrn(site_hrn, slice['name'])
        # Try to locate the slice_hrn in the SFA records
        slice_record = self.locate_by_type_hrn ('slice', slice_hrn)
        
        if not slice_record:
            # Create/Import record for the slice
            try:
                #Create a keypair for the slice
                pkey = Keypair(create=True)
                # Obtain parameters
                urn = hrn_to_urn(slice_hrn, 'slice')
                slice_gid = self.auth_hierarchy.create_gid(urn, create_uuid(), pkey)
                # Create record for the slice and add it to the Registry
                slice_record = RegSlice (hrn=slice_hrn, gid=slice_gid, 
                                         pointer=slice['id'],
                                         authority=get_authority(slice_hrn))
                slice_record.just_created()
                global_dbsession.add(slice_record)
                global_dbsession.commit()
                self.logger.info("CLabImporter: imported slice: %s" % slice_hrn)  
                self.remember_record ( slice_record )
            except:
                self.logger.log_exc("CLabImporter: failed to import slice")
        else:
            # Slice record already in the SFA registry. Update?
            self.logger.warning ("Slice already existing in SFA Registry")
            pass
        
        # Get current users associated with the slice
        users_of_slice = shell.get_users_by_slice(slice)
        # record current users associated with the slice
        slice_record.reg_researchers = \
            [ self.locate_by_type_pointer ('user',user['id']) for user in users_of_slice]
        global_dbsession.commit()
        
        
