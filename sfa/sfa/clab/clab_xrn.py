'''
Created on 06/02/2014

@author: gerard
'''


from sfa.util.xrn import Xrn

'''
Methods and classes for XRN management in C-Lab
'''

def type_of_urn(urn):
    """
    Returns the type of the given urn (node, slice, sliver)
    
    :param urn: URN to discover the type
    :type string
    
    :returns type of the URN (node, slice, sliver, user, authority)
    """
    return Xrn(urn).get_type()


def xrn_object(root_auth, hostname):
    """
    Creates a valid xrn object from the node's hostname and the authority
    of the SFA server.

    :param hostname: the node's hostname
    :type string
    
    :param root_auth: the SFA root authority
    :type string

    :returns: the C-Lab node's xrn
    :rtype: Xrn
    """
    return Xrn('.'.join([root_auth, Xrn.escape(hostname)]), type='node')
    

def xrn_to_hostname(xrn):
    """
    Returns a node's hostname from its xrn
    NOTE: If it is a URN, it must include the 'type' field
    
    :param xrn: The nodes xrn identifier
    :type Xrn (from sfa.util.xrn)

    :returns: node's hostname
    :rtype: string
    """
    return Xrn.unescape(Xrn(xrn=xrn, type='node').get_leaf())


def hostname_to_hrn (auth, hostname):
    """
    Turns node hostname into hrn.
    
    :param auth: Site authority
    :type string
    
    :param hostname: Node hostname   
    :type string

    :returns: Node's hrn
    :rtype: string
    """
    escaped_hostname = escape_testbed_obj_names(hostname)
    return ClabXrn(auth=auth, hostname=escaped_hostname).get_hrn()

def hostname_to_urn(auth, hostname):
    """
    Turns node hostname into urn.
    
    :param auth: Site authority.
    :type string
    
    :param hostname: Node hostname.
    :type string.

    :returns: Node's urn.
    :rtype: string
    """
    return ClabXrn(auth=auth, hostname=hostname).get_urn()


def slicename_to_hrn (auth, slicename):
    """
    Turns slice name into hrn.
    
    :param auth: Site authority
    :type string
    
    :param slicename: Slice name
    :type string

    :returns: Slice's hrn
    :rtype: string
    """
    escaped_slicename = escape_testbed_obj_names(slicename)
    return ClabXrn(auth=auth, slicename=escaped_slicename).get_hrn()


def slicename_to_urn (auth, slicename):
    """
    Turns Slice name into urn.
    
    :param auth: Site authority
    :type string
    
    :param slicename: Slice name
    :type string

    :returns: Slice's urn.
    :rtype: string
    """
    return ClabXrn(auth=auth, slicename=slicename).get_urn()


def urn_to_slicename (urn):
    """
    Turns URN into a slice name (C-Lab specific)
    
    :param urn: URN of the Slice
    :type string

    :returns: Slice name.
    :rtype: string
    """
    return ClabXrn(xrn=urn, type='slice').get_slicename()


def hrn_to_slicename (hrn):
    """
    Turns HRN into a slice name (C-Lab specific)
    
    :param hrn: HRN of the Slice
    :type string

    :returns: Slice name.
    :rtype: string
    """
    return ClabXrn(xrn=hrn, type='slice').get_slicename()


def urn_to_nodename (urn):
    """
    Turns URN into a node name (C-Lab specific)
    
    :param urn: URN of the Node
    :type string

    :returns: Node name.
    :rtype: string
    """
    return xrn_to_hostname(urn)


def hrn_to_nodename (hrn):
    """
    Turns HRN into a node name (C-Lab specific)
    
    :param hrn: HRN of the Node
    :type string

    :returns: Node name.
    :rtype: string
    """
    return xrn_to_hostname(hrn)


def slivername_to_hrn (auth, slivername):
    """
    Turns Sliver name into hrn.
    
    :param auth: Site authority
    :type string
    
    :param slivername: Sliver name
    :type string

    :returns: Sliver's hrn.
    :rtype: string
    """
    escaped_slivername = escape_testbed_obj_names(slivername)
    ClabXrn(auth=auth, slivername=escaped_slivername).get_hrn()

def slivername_to_urn (auth, slivername):
    """
    Turns Sliver name into urn.
    
    :param auth: Site authority
    :type string
    
    :param slivername: Slice name
    :type string

    :returns: Sliver's urn.
    :rtype: string
    """
    return ClabXrn(auth=auth, slivername=slivername).get_urn()

def urn_to_slivername (urn):
    """
    Turns URN into a sliver name (C-Lab specific)
    
    :param urn: URN of the Sliver
    :type string

    :returns: Sliver name.
    :rtype: string
    """
    return ClabXrn(xrn=urn, type='sliver').get_slivername()

def hrn_to_slivername (hrn):
    """
    Turns HRN into a sliver name (C-Lab specific)
    
    :param hrn: HRN of the Sliver
    :type string

    :returns: Sliver name.
    :rtype: string
    """
    return ClabXrn(xrn=hrn, type='sliver').get_slivername()


def xrn_slivername_to_clab_slivername(slivername):
    """
    Helper method to replace the character '@' from C-Lab sliver name
    by the character 'a' for GENI xrn
    
    :param slivername: C-Lab sliver name
    :type string

    :returns: GENI xrn Sliver name.
    :rtype: string
    """
    # sliceid a nodeif --> sliceid @ nodeid
    return slivername.replace('a', '@')


def clab_slivername_to_xrn_slivername(slivername):
    """
    Helper method to replace the character 'a' from GENI xrn sliver name
    by the character 'a' for C-Lab sliver name
    
    :param slivername: GENI xrn sliver name
    :type string

    :returns: C-lab Sliver name.
    :rtype: string
    """
    # sliceid @ nodeif --> sliceid a nodeid
    return slivername.replace('@', 'a')


def hrn_to_authname (hrn):
    """
    Gets the authority name from an HRN
    
    :param hrn: HRN whose authority is got
    :type string

    :returns: authority name name.
    :rtype: string
    """
    return Xrn(xrn=hrn).get_authority_hrn()

def username_to_hrn (auth, username):
    """
    Turns user name into hrn.
    
    :param auth: Site authority
    :type string
    
    :param username: Node username   
    :type string

    :returns: Node's hrn
    :rtype: string
    """
    escaped_username = escape_testbed_obj_names(username)
    return ClabXrn(auth=auth, username=escaped_username).get_hrn()

def username_to_urn(auth, username):
    """
    Turns user name into urn.
    
    :param auth: Site authority.
    :type string
    
    :param username: Node username.
    :type string.

    :returns: Node's urn.
    :rtype: string
    """
    return ClabXrn(auth=auth, username=username).get_urn()

def escape_testbed_obj_names(object_name):
    """
    Escape names of objects from the testbed (nodes, users, slices, slivers...) 
    to avoid/replace characters/sequences of characters that might produce errors 
    or missinterpretations when obtaining the correspondind hrns. 
    
    :param object_name: testbed-specific name of an object (user, node, slice, sliver...)
    :type string.

    :returns: escaped name replaing dangerous characters
    :rtype: string
    """
    escaped_name = object_name
    
    # Replace "." with double underscore "__"
    # "." gives problems because is interpreted as subauthority
    if "." in object_name:
        escaped_name = object_name.replace(".","__")
    
    return escaped_name
    

###########################################
# Special translation methods using driver
# URN to URI, get_by_urn methods
###########################################

def urn_to_uri(driver, urn):
    '''
    Turns a URN of an object to the uri that corresponds to the object
    
    :param driver: reference to a ClabDriver instance
    :type ClabDriver
    
    :param urn: URN being translated
    :type string

    :returns: C-Lab URI of the object
    :rtype: string
    '''
    if type_of_urn(urn) == 'node':
        node = get_node_by_urn(driver, urn)
        uri = node['uri']
    elif type_of_urn(urn) == 'slice':
        slice = get_slice_by_urn(driver, urn)
        uri = slice['uri'] 
    elif type_of_urn(urn) == 'sliver':
        sliver = get_sliver_by_urn(driver, urn)
        uri = sliver['uri'] 
    return uri


def get_slice_by_urn(driver, urn):
    '''
    Return the slice clab-specific dictionary that corresponds to the 
    given urn
        
    :param driver: reference to a ClabDriver instance
    :type ClabDriver
    
    :param urn: URN of the slice
    :type string

    :returns: C-Lab slice dictionary
    :rtype: dict
    '''
    slicename=urn_to_slicename(urn)
    return driver.testbed_shell.get_slice_by(slice_name=slicename)


def get_slice_by_sliver_urn(driver, urn):
    '''
    Return the slice clab-specific dictionary where the sliver identified by
    the given urn is contained
        
    :param driver: reference to a ClabDriver instance
    :type ClabDriver
    
    :param urn: URN of the sliver
    :type string

    :returns: C-Lab slice dictionary
    :rtype: dict
    '''
    slivername = urn_to_slivername(urn)
    # slivername = sliceid @ nodeid
    sliver = driver.testbed_shell.get_sliver_by(sliver_name=slivername)
    slice_uri = sliver['slice']['uri']
    return driver.testbed_shell.get_slice_by(slice_uri=slice_uri)


def get_node_by_urn(driver, urn):
    '''
    Return the node clab-specific dictionary that corresponds to the 
    given urn
        
    :param driver: reference to a ClabDriver instance
    :type ClabDriver
    
    :param urn: URN of the node
    :type string

    :returns: C-Lab node dictionary
    :rtype: dict
    '''
    nodename=urn_to_nodename(urn)
    return driver.testbed_shell.get_node_by(node_name=nodename)


def get_sliver_by_urn(driver, urn):
    '''
    Return the sliver clab-specific dictionary that corresponds to the 
    given urn
        
    :param driver: reference to a ClabDriver instance
    :type ClabDriver
    
    :param urn: URN of the sliver
    :type string

    :returns: C-Lab sliver dictionary
    :rtype: dict
    '''
    #sliver_name=sliver_id   --->  slice_id @ node_id
    slivername=urn_to_slivername(urn)
    return driver.testbed_shell.get_sliver_by(sliver_name=slivername)

#####################################################


class ClabXrn (Xrn):
    """
    Defines methods to translate between XRN and object names specific of the C-Lab testbed.
    Extends XRN (generic SFA class for XRN management)
    """
    
    @staticmethod
    def site_hrn (auth):
        return auth

    def __init__ (self, auth=None, hostname=None, slicename=None, slivername=None, username=None, **kwargs):
        
        if hostname is not None:
            self.type = 'node'
            self.hrn = '.'.join( [auth, Xrn.escape(hostname)] )
            self.hrn_to_urn()

        elif slicename is not None:
            self.type = 'slice'
            self.hrn = '.'.join([auth, slicename])
            self.hrn_to_urn()
        
        elif slivername is not None:
            self.type = 'sliver'
            # Reformat sliver name
            xrn_slivername = clab_slivername_to_xrn_slivername(slivername)
            self.hrn = '.'.join([auth, xrn_slivername])
            self.hrn_to_urn()
            
        elif username is not None:
            self.type = 'user'
            self.hrn = '.'.join([auth, username])
            self.hrn_to_urn()

        else:
            Xrn.__init__ (self, **kwargs)
            
    
    def get_slicename(self):
        return self.get_leaf()
    
    def get_slivername(self):
        xrn_slivername = self.get_leaf()
        return xrn_slivername_to_clab_slivername(xrn_slivername)


