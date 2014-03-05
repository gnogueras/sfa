'''
Created on 15/02/2014

@author: gerard
'''
#########################################################
# clab_aggregate
#########################################################

def allocate(self, slice_urn, credentials, rspec_string, options={}):
        '''
        Function to allocate/reserve the resources described in the rspec_string for a sliver 
        that will belong to the slice specified by the slice_urn argument.
        
        Returns the following struct:
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
    
        NOTE: ALLOCATE (GENI) = REGISTER (C-LAB)
              Create slivers in Register state.
        '''
        # Verify slice exist
            
        # Get slice uri
        slice_uri = self.get_slice_by_urn(slice_urn)['uri']
               
        # parse RSpec (if rspec_string argument)
        rspec = RSpec(rspec_string)
        # nodes in which the slivers will be created (list of dict)
        nodes_with_slivers = rspec.version.get_nodes_with_slivers()
        # ignore slice attributes...
        requested_attributes = rspec.version.get_slice_attributes()
        
        # Translate sliver RSpecs to C-Lab slivers
        # Each element node_with_sliver will create a sliver belonging to the slice in the corresponding node
        for node_with_sliver in nodes_with_slivers:            
            # bound_node
            nodename = node_with_sliver['client_id']
            bound_node_uri = self.driver.testbed_shell.get_node_by_name(nodename)['uri']
            
            # otherwise, select any node available for this slice
            if not bound_node_uri: bound_node_uri = self.driver.testbed_shell.get_available_nodes_for_slice(slice_uri)[0]['uri']
            
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
            created_sliver = self.driver.testbed_shell.create_sliver(slice_uri, bound_node_uri, interfaces_definition, properties)
            
        # prepare return struct 
        return self.describe([slice_urn], version=rspec.version)



#########################################################
# clab_dirver
#########################################################

    ########################################
    #####      registry oriented       #####
    ########################################

    def augment_records_with_testbed_info (self, sfa_records):
        '''
        Fill the given sfa record s with information from the C-Lab testbed
        '''
        return self.fill_record_info (sfa_records)
    
    
    def register (self, sfa_record, hrn, pub_key=None):
        '''
        Register a new object (record) within the registry. In addition to being stored at the SFA
        level, the appropriate records will also be created at the testbed level.
        The supported object types are: node, slice, user
        sfa_record = { 'name':'name_of_the_entity', 'type':'type_of_the_entity' 'group':'group_entity_belongs_to' }
        hrn: hrn of the resource
        pub_key: applies if user type
        Return id (C-Lab id) of the created object
        '''
        if sfa_record['type'] == 'node':
            try:
                node_id = self.testbed_shell.get_node_by(node_name=sfa_record['name']).get('id', None)
            except Exception: 
                # Exception raised if the node is not found (does not exist)
                node_id = self.testbed_shell.create_node(sfa_record).get('id', None)
            return node_id

        elif sfa_record['type'] == 'slice':
            try:
                slice_id = self.testbed_shell.get_slice_by(slice_name=sfa_record['name']).get('id', None)
            except Exception:
                # Exception raised if the slice is not found (does not exist)
                slice_id = self.testbed_shell.create_slice(sfa_record['name']).get('id', None)
            return slice_id
            
        elif sfa_record['type'] == 'user':
            # REGISTER USERS IN ORM???
            pass

    
        
    def remove (self, sfa_record):
        '''
        Remove the named object from the registry. If the object also represents a testbed object,
        the corresponding record will be also removed from the testbed.
        '''
        # If uri field in the record, delete directly by uri
        if 'uri' in sfa_record:
            ret = self.testbed_shell.delete(sfa_record['uri'])
            
        #otherwise, get the type and then the uri of the object    
        elif sfa_record['type'] == 'node':
            node_id = sfa_record['pointer']
            node_uri = self.testbed_shell.get_nodes({'id' : node_id})[0]['uri']
            ret = self.testbed_shell.delete(node_uri)
            
        elif sfa_record['type'] == 'slice':
            slice_id = sfa_record['pointer']
            slice_uri = self.testbed_shell.get_slices({'id' : slice_id})[0]['uri']
            ret = self.testbed_shell.delete(slice_uri)
            
        elif sfa_record['type'] == 'user':
            user_id = sfa_record['pointer']
            user_uri = self.testbed_shell.get_users({'id' : user_id})[0]['uri']
            ret = self.testbed_shell.delete(user_uri)
        
        return ret
    
    
    def update (self, old_sfa_record, new_sfa_record, hrn, new_key):
        '''
        Update a object (record) in the registry. This might also update the tested information
        associated with the record. 
        '''
        pointer = old_sfa_record['pointer']
        type = old_sfa_record['type']
        
        new_clab_record = self.sfa_fields_to_clab_fields(type, hrn, new_sfa_record)

        # new_key implemented for users only
        if new_key and type not in [ 'user' ]:
            raise UnknownSfaType(type)

        if type == "slice":
            if 'name' in new_sfa_record:
                filtered_slices = self.testbed_shell.get_slices({'id': pointer})
                if not filtered_slices:
                    # Slice not found
                    raise Exception 
                slice_uri = filtered_slices[0]['uri']
                self.testbed_shell.update_slice(slice_uri, {'name': new_sfa_record['name']})
    
        elif type == "user":
            update_fields = {}
            if 'name' in new_sfa_record:
                update_fields['name'] = new_sfa_record['name']
            user_uri = self.testbed_shell.get_users({'id': pointer})[0]['uri']
            self.testbed_shell.update_user(user_uri, update_fields) 
    
            #if new_key:
                # needs to be improved 
                #self.shell.addUserKey({'user_id': pointer, 'key': new_key}) 
    
        elif type == "node":
            node_uri = self.testbed_shell.get_nodes({'id': pointer})[0]['uri']
            self.testbed_shell.update_node(node_uri, new_sfa_record)

        return True


    
    def update_relation (self, subject_type, target_type, relation_name, subject_id, target_ids):
        '''
        Update the relations between objects in the testbed. 
        Typically it is used to add/change roles of users with respect to some resources, 
        e.g. defined the role of researcher for a user in a given slice. 
            
            subject_type – resource type (slice, node...) for which the relation is being updated. Subject of the relation update.
            target_type – resource/entity (user) whose relation with respect to the resource indicated in subject is being changed. 
                          Target of the relation updated.
            relation_name – new role for the target entity with respect to the subject resource. (researcher, owner...)
            subject_id – ID of the subject resource for which the relation is being changed (id of the slice)
            target_ids – ID or list of IDs for the entity or entities whose relation with respect to the subject resource is being updated. 
        
        '''
        # Supported: change relation type of a User for a Slice
        if subject_type =='slice' and target_type == 'user':
            # obtain subject slice
            subject = self.testbed_shell.get_slices ({'id': subject_id}, [])[0]
            # Obtain group_uri the slice belongs to 
            group_uri = subject['group']['uri']
            
            # For each target_id (user_id) that needs its role to be changed
            for target_id in target_ids:
                # Get the current group roles of the user
                user = self.testbed_shell.get_users({'id':target_id})[0]
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
                user.update(group_roles=group_roles)

        else:
            logger.info('unexpected relation %s to maintain, %s -> %s'%(relation_name,subject_type,target_type))
                                                                            




#########################################################
# clab_xrn
#########################################################





#########################################################
# clab_shell
#########################################################

    def get_slivers_by_node(self, node=None, node_uri=None):
        '''
        Function to get the slivers from a specific node or node uri
        '''
        
    
        if node:
            # obtain slivers uri
            sliver_uris = [sliver['uri'] for sliver in node['slivers']]
            slivers = []
            for uri in sliver_uris:
                slivers.append(self.get_sliver_by(sliver_uri=uri))
            #slivers = controller.slivers.retrieve().serialize()
            #slivers = [sliver for sliver in slivers if sliver['node']['uri']==node['uri']]
        elif node_uri:
            # Check if node_uri exist and is a valid uri
            try:
                controller.retrieve(node_uri).serialize()
            except controller.ResponseStatusError as e:
                raise ResourceNotFound(node_uri, e.message)
            except Exception as e:
                raise InvalidURI(node_uri, e.message) 
            # Obtain slivers of the node
            slivers = controller.slivers.retrieve().serialize()
            slivers = [sliver for sliver in slivers if sliver['node']['uri']==node_uri]
        return slivers



def update_sliver_state(self, sliver_uri, state):
        '''
        Function that updates the sliver set_state to the specified state.
        The state argument is a C-Lab specific state (register, deploy, start)
        '''
        # BUG! It does not work this way:
        #sliver = controller.retrieve(sliver_uri)
        #sliver.update(set_state=state)
        
        # Alternative way
        #slivers = controller.slivers.retrieve()
        #sliver = [sliver for sliver in slivers if sliver.uri==sliver_uri][0]
        #sliver.update(set_state=state)
        
        # Simpler alternative way
        try:
            sliver = controller.retrieve(sliver_uri)
        except controller.ResponseStatusError as e:
            raise ResourceNotFound(sliver_uri, e.message)
        except Exception as e:
            raise InvalidURI(sliver_uri, e.message)
        sliver.set_state=state
        sliver.save()
        return True

#########################################################
# clab_slices
#########################################################

