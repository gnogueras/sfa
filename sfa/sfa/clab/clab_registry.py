# -*- coding: utf-8 -*-
'''
Created on 20/02/2014

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

from sfa.clab.clab_aggregate import ClabAggregate
from sfa.clab.clab_shell import ClabShell
from sfa.clab.clab_xrn import slicename_to_hrn, hostname_to_hrn



class ClabRegistry:
    """
    Registry class for C-Lab. 
    API v3
    """
    
    def __init__(self, driver):
        self.driver = driver
    
    
    def augment_records_with_testbed_info (self, sfa_records):
        '''
        Fill the given sfa records with information from the C-Lab testbed
        
        :param sfa_records: list of dictionaries that implement the sfa_records being augmented
        :type list
        
        :returns list of sfa_records augmented with testbed information
        :rtype list
        '''
        return self.fill_record_info (sfa_records)
    
    
    def register (self, sfa_record, hrn, pub_key=None):
        '''
        Register a new object (record) within the registry. In addition to being stored at the SFA
        level, the appropriate records will also be created at the testbed level.
        The supported object types are: node, slice, user
        
        :param sfa_record: SFA record of the entity being registered. It must contain at least:
            { 'name':'name_of_the_entity', 'type':'type_of_the_entity' 'group':'group_entity_belongs_to' }
        :type dict
        
        :param hrn: hrn of the resource being registered
        :type string
        
        :param pub_key: public key of the user (if apply)
        :type string
        
        :returns C-Lab identifier (id) of the created entity
        :rtype int
        '''
        print "Register method in ClabRegistry"
        # Get name of the entity being registered
        entity_name = sfa_record.get('name', get_leaf(hrn))
        if sfa_record['type'] == 'node':
            try:
                node_id = self.driver.testbed_shell.get_node_by(node_name=entity_name).get('id', None)
            except Exception: 
                # Create the node if does not exist
                node_id = self.driver.testbed_shell.create_node(entity_name, sfa_record).get('id', None)
            return node_id

        elif sfa_record['type'] == 'slice':
            try:
                slice_id = self.driver.testbed_shell.get_slice_by(slice_name=entity_name).get('id', None)
            except Exception:
                # Create the slice if does not exist
                print "Calling shell.create_slice with name %s"%(entity_name)
                print sfa_record
                slice_id = self.driver.testbed_shell.create_slice(entity_name, fields=sfa_record).get('id', None)
            return slice_id
            
        elif sfa_record['type'] == 'user':
            try:
                user_id = self.driver.testbed_shell.get_users({'name':entity_name})[0].get('id', None)
            except Exception:
                # Create the user if does not exist
                print "Calling shell.create_user with name %s"%(entity_name)
                print sfa_record
                user_id = self.driver.testbed_shell.create_user(entity_name).get('id', None)
            return user_id
    
        
    def remove (self, sfa_record):
        '''
        Remove the named object from the registry. If the object also represents a testbed object,
        the corresponding record will be also removed from the testbed.
        
        :param sfa_record: dictionary implementing the SFA record of the entity being removed
        :type dict
        
        :returns booelan indicating the success of the operation
        :rtype boolean
        '''
        # If uri field in the record, delete directly by uri
        if 'uri' in sfa_record:
            ret = self.driver.testbed_shell.delete(sfa_record['uri'])
            
        #otherwise, get the type and then the uri of the object    
        elif sfa_record['type'] == 'node':
            node_id = sfa_record['pointer']
            if isinstance(node_id, str): 
                node_id=int(node_id)
            node_uri = self.driver.testbed_shell.get_nodes({'id' : node_id})[0]['uri']
            ret = self.driver.testbed_shell.delete(node_uri)
            
        elif sfa_record['type'] == 'slice':
            slice_id = sfa_record['pointer']
            if isinstance(slice_id, str): 
                slice_id=int(slice_id)
            slice_uri = self.driver.testbed_shell.get_slices({'id' : slice_id})[0]['uri']
            ret = self.driver.testbed_shell.delete(slice_uri)
            
        elif sfa_record['type'] == 'user':
            user_id = sfa_record['pointer']
            user_uri = self.driver.testbed_shell.get_users({'id' : user_id})[0]['uri']
            ret = self.driver.testbed_shell.delete(user_uri)
        
        return ret
    
    
    def update (self, old_sfa_record, new_sfa_record, hrn, new_key):
        '''
        Update a object (record) in the registry. This might also update the tested information
        associated with the record. 
        
        :param old_sfa_record: SFA record of the entity being updated
        :type dict
        
        :param new_sfa_record: new SFA record to update the old SFA record
        :type dict
        
        :param hrn: hrn of the resource being updated
        :type string
        
        :param new_key: new public key for the user (if apply)
        :type string
        
        :returns boolean value indicating the success of the operation
        :rtype boolean
        '''
        pointer = old_sfa_record['pointer']
        if isinstance(pointer, str):
            pointer = int(pointer)
        type = old_sfa_record['type']
        
        clab_updated_fields = self.sfa_fields_to_clab_fields(type, hrn, new_sfa_record)

        # new_key implemented for users only
        #if new_key and type not in [ 'user' ]:
        #    raise UnknownSfaType(type)

        if type == "slice":
            filtered_slices = self.driver.testbed_shell.get_slices({'id': pointer})
            if not filtered_slices:
                raise RecordNotFound('Slice with id %s'%pointer) # Slice not found 
            slice_uri = filtered_slices[0]['uri']
            return self.driver.testbed_shell.update_slice(slice_uri, clab_updated_fields)
    
        elif type == "user":
            filtered_users = self.driver.testbed_shell.get_users({'id': pointer})
            if not filtered_slices:
                raise RecordNotFound('User with id %s'%pointer) # User not found 
            user_uri = filtered_users[0]['uri']
            return self.driver.testbed_shell.update_user(user_uri, clab_updated_fields) 
    
            #if new_key:
                # needs to be improved 
                #self.shell.addUserKey({'user_id': pointer, 'key': new_key}) 
    
        elif type == "node":
            filtered_nodes = self.driver.testbed_shell.get_nodes({'id': pointer})
            if not filtered_nodes:
                raise RecordNotFound('Node with id %s'%pointer) # Node not found 
            node_uri = filtered_nodes[0]['uri']
            return self.driver.testbed_shell.update_node(node_uri, clab_updated_fields)

        return False


    
    def update_relation (self, subject_type, target_type, relation_name, subject_id, target_ids):
        '''
        Update the relations between objects in the testbed. 
        Typically it is used to add/change roles of users with respect to some resources, 
        e.g. defined the role of researcher for a user in a given slice. 
            
        :param subject_type: resource type (slice, node...) for which the relation is being updated. Subject of the relation update.
        :type string
        
        :param target_type: resource/entity (user) whose relation with respect to the resource indicated in subject is being changed. 
            Target of the relation updated.
        :type string
        
        :param relation_name: new role for the target entity with respect to the subject resource. (researcher, owner...)
        :type string
        
        :param subject_id: ID of the subject resource for which the relation is being changed (id of the slice)
        :type string OR int
        
        :param target_ids: ID or list of IDs for the entity or entities whose relation with respect to the subject resource is being updated. 
        :type list
        
        :returns boolean value indicating the success of the operation
        :rtype boolean
        '''
        # Supported: change relation type of a User for a Slice
        if subject_type =='slice' and target_type == 'user':
            # obtain subject slice
            if isinstance(subject_id, str):
                subject_id = int(subject_id)
            filtered_subjects = self.driver.testbed_shell.get_slices ({'id': subject_id})
            if not filtered_subjects:
                raise RecordNotFound('Slice with id %s'%subject_id)
            subject = filtered_subjects[0]
            # Obtain group_uri the slice belongs to 
            group_uri = subject['group']['uri']
            
            if not isinstance(target_ids, list):
                target_ids = [target_ids]
            # For each target_id (user_id) that needs its role to be changed
            for target_id in target_ids:
                # Get the current group roles of the user
                if isinstance(target_id, str):
                    target_id = int(target_id)
                user = self.driver.testbed_shell.get_users({'id':target_id})[0]
                group_roles = user['group_roles']
                # Change the roles according to the relation_update for the user
                # The roles of the group that the subject slice belogs to 
                for role in group_roles:
                    # Select the group role of the group that the slice belongs to
                    if role['group']['uri']==group_uri:
                        # Prepare new relation
                        if relation_name == 'researcher':
                            role['is_researcher']=True
                        elif relation_name == 'technician':
                            role['is_technician']=True
                        break
                # Update the user with the new group_roles 
                return self.driver.testbed_shell.update_user(user['uri'], {'group_roles':group_roles})
                
        else: 
            raise SfaNotImplemented('Registry')
    
    
                
    ##############################################
    #####      auxiliary/helper methods      #####
    ##############################################       
    
    def fill_record_info(self, records):
        """
        Given a (list of) SFA record, fill in the C-Lab specific 
        and SFA specific fields in the record.
        
        :param records: list of SFA records to be filled
        :type list
        
        :returns list of filled SFA records
        :rtype list 
        """
        if not isinstance(records, list):
            records = [records]

        self.fill_record_clab_info(records)
        self.fill_record_hrns(records)
        self.fill_record_sfa_info(records)
        return records

    def fill_record_clab_info(self, records):
        """
        Fill in the C-Lab specific fields of a SFA record. This
        involves calling the appropriate C-Lab API method to retrieve the 
        database record for the object.
            
        :param record: list of SFA records to be filled in
        :type list
        
        :returns list of SFA records filled with testbed information
        :rtype list     
        """
        
        # get ids by type
        node_ids, slice_ids = [], [] 
        user_ids, key_ids = [], []
        type_map = {'node': node_ids, 'slice': slice_ids, 'user': user_ids}
                  
        for record in records:
            for type in type_map:
                if type == record['type']:
                    type_map[type].append(record['pointer'])

        # get clab records
        nodes, slices, users, keys = {}, {}, {}, {}
        if node_ids:
            all_nodes = self.convert_id(self.driver.testbed_shell.get_nodes())
            node_list =  [node for node in all_nodes if node['id'] in node_ids]
            nodes = self.list_to_dict(node_list, 'id')
            
        if slice_ids:
            all_slices = self.convert_id(self.driver.testbed_shell.get_slices())
            slice_list =  [slice for slice in all_slices if slice['id'] in slice_ids]
            slices = self.list_to_dict(slice_list, 'id')
            
        if user_ids:
            all_users = self.convert_id(self.driver.testbed_shell.get_users())
            user_list = [user for user in all_users if user['id'] in user_ids] 
            users = self.list_to_dict(user_list, 'id')

        clab_records = {'node': nodes, 'slice': slices, 'user': users}


        # fill record info
        for record in records:
            if record['pointer'] == -1:
                continue
           
            for type in clab_records:
                if record['type'] == type:
                    if record['pointer'] in clab_records[type]:
                        record.update(clab_records[type][record['pointer']])
                        break
            # fill in key info
            #if record['type'] == 'user':
            #    if record['pointer'] in clab_records['user']:
            #        record['keys'] = clab_records['user'][record['pointer']]['keys']

        return records
    
    
    def fill_record_hrns(self, records):
        """
        Convert C-Lab names of the records in the list to hrns
        
        :param record: list of SFA records whose names are converted
        :type list
        
        :returns list of SFA records filled with hrn
        :rtype list 
        """
        # get ids
        slice_ids, user_ids, node_ids = [], [], []
        for record in records:
            if 'user_ids' in record:
                user_ids.extend(record['user_ids'])
            if 'slice_ids' in record:
                slice_ids.extend(record['slice_ids'])
            if 'node_ids' in record:
                node_ids.extend(record['node_ids'])
        
        # get clab records
        nodes, slices, users, keys = {}, {}, {}, {}
        if node_ids:
            all_nodes = self.convert_id(self.driver.testbed_shell.get_nodes())
            node_list =  [node for node in all_nodes if node['id'] in node_ids]
            nodes = self.list_to_dict(node_list, 'id')
            
        if slice_ids:
            all_slices = self.convert_id(self.driver.testbed_shell.get_slices())
            slice_list =  [slice for slice in all_slices if slice['id'] in slice_ids]
            slices = self.list_to_dict(slice_list, 'id')
            
        if user_ids:
            all_users = self.convert_id(self.driver.testbed_shell.get_users())
            user_list = [user for user in all_users if user['id'] in user_ids] 
            users = self.list_to_dict(user_list, 'id')       

        # convert ids to hrns
        for record in records:
            # get all relevant data
            type = record['type']
            pointer = record['pointer']
            auth_hrn = self.driver.AUTHORITY
            if pointer == -1:
                continue
            if 'user_ids' in record:
                usernames = [users[user_id]['name'] for user_id in record['user_ids'] if user_id in  users]
                user_hrns = [".".join([auth_hrn, username]) for username in usernames]
                record['users'] = user_hrns 
            if 'slice_ids' in record:
                slicenames = [slices[slice_id]['name'] for slice_id in record['slice_ids'] if slice_id in slices]
                slice_hrns = [slicename_to_hrn(auth_hrn, slicename) for slicename in slicenames]
                record['slices'] = slice_hrns
            if 'node_ids' in record:
                hostnames = [nodes[node_id]['name'] for node_id in record['node_ids'] if node_id in nodes]
                node_hrns = [hostname_to_hrn(auth_hrn, hostname) for hostname in hostnames]
                record['nodes'] = node_hrns

            if 'expires' in record:
                date = utcparse(record['expires'])
                datestring = datetime_to_string(date)
                record['expires'] = datestring 
            
        return records
    
    
    def fill_record_sfa_info(self, records):
        """
        Fill in the records with SFA specific information.
        
        :param record: list of SFA records being field
        :type list
        
        :returns list of SFA records filled with SFA information
        :rtype list 
        """
        def startswith(prefix, values):
            return [value for value in values if value.startswith(prefix)]

        # get user ids
        user_ids = []
        for record in records:
            user_ids.extend(record.get("user_ids", []))
        
        # get the registry records
        user_list, users = [], {}
        #user_list = self.api.dbsession().query(RegRecord).filter(RegRecord.pointer.in_(user_ids)).all()
        # create a hrns keyed on the sfa record's pointer.
        # Its possible for multiple records to have the same pointer so
        # the dict's value will be a list of hrns.
        users = defaultdict(list)
        for user in user_list:
            users[user.pointer].append(user)

        # get the C-Lab records
        clab_user_list, clab_users = [], {}
        clab_all_users = self.convert_id(self.driver.testbed_shell.get_users())
        clab_user_list = [user for user in clab_all_users if user['id'] in user_ids]
        clab_users = self.list_to_dict(clab_user_list, 'id')

        # fill sfa info
        for record in records:
            if record['pointer'] == -1:
                continue 

            sfa_info = {}
            type = record['type']
            #logger.info("fill_record_sfa_info - incoming record typed %s"%type)
            if (type == "slice"):
                # all slice users are researchers
                record['geni_urn'] = hrn_to_urn(record['hrn'], 'slice')
                record['researcher'] = []
                for user_id in record.get('user_ids', []):
                    hrns = [user.hrn for user in users[user_id]]
                    record['researcher'].extend(hrns)                
                
            elif (type == "node"):
                sfa_info['dns'] = record.get("hostname", "")
                # xxx TODO: URI, LatLong, IP, DNS
    
            elif (type == "user"):
                logger.info('setting user.email')
                sfa_info['email'] = record.get("email", "")
                sfa_info['geni_urn'] = hrn_to_urn(record['hrn'], 'user')
                sfa_info['geni_certificate'] = record['gid'] 
                # xxx TODO: PostalAddress, Phone
            record.update(sfa_info)   
    
    
    def  sfa_fields_to_clab_fields(self, type, hrn, new_sfa_record):
        '''
        Convert SFA record into a C-Lab dict corresponding to the specific type 
        Used in update operation
        
        :param type: type of the record being updated (node, slice, user)
        :type string
        
        :param hrn: hrn of the resource being updated
        :type string
        
        :param new_sfa_record: SFA record that needs to be converted
        :type dict
        
        :returns C-lab specific dictionary 
        :type dict
        '''
        #fields = [ 'type', 'hrn', 'gid', 'authority', 'peer_authority' ]
        clab_dict = {}
        if 'name' in new_sfa_record:
            clab_dict['name'] = new_sfa_record['name']
        if 'description' in new_sfa_record:
            clab_dict['description'] = new_sfa_record['description']
        if type=='node':
            pass 
        elif type=='slice':
            pass
        elif type=='user':
            pass
        return clab_dict
    
    
    def convert_id (self, list_of_dict):
        """
        Converts the field 'id' of each dictionary in the list from string to integer
        
        :param list_of_dicts: list of dictionaries whose id fields are being converted
        :type list
        
        :returns list of dictionaries with integer id values
        :type list
        """
        for dictionary in list_of_dict:
            if 'id' in dictionary and isinstance(dictionary['id'], str):
                dictionary['id'] = int(dictionary['id'])
        return list_of_dict
    
    
    def list_to_dict(self, recs, key):
        """
        Convert a list of dictionaries into a dictionary keyed on the 
        specified dictionary key
        
        :param recs: list of dictionaries being converted
        :type list
        
        :param key: field of the dictionaries that will be used as a key for the new dictionary
        :type string 
        """
        return dict ( [ (rec[key],rec) for rec in recs ] )


                                                                            
    