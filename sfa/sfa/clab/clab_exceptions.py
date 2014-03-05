'''
Created on 19/02/2014

@author: gerard
'''

# Module that defines different exceptions to encapsulate possible errors or problems
# during the executions of the use cases and scenarios for C-Lab SFAWrap
# The exceptions defined are C-Lab specific. It means that they are from the testbed side.
# The exceptions defined are used in the CLabShell class to encapsulate errors from the 
# lower layer ORM. 
# The exceptions might be translated to SFA exceptions/fault (if needed) 
# in clab_aggergate and clab_driver modules.

class MalformedURI (Exception):
    '''
    Exception indicating a malformed URI received as argument that does not match the schema request.
    Encapsulates requests.exceptions.MissingSchema from ORM
    '''
    # 
    def __init__(self, uri, message=None):
        Exception.__init__(self, message)
        self.urn = uri
        self.clab_message = 'Malformed URI that does not pass the schema validation. (%s)'%(uri)
    def __str__(self):
        return repr(self.clab_message)

class UnexistingURI (Exception):
    '''
    Exception indicating a unexisting URI received as argument. 
    Encapsulates requests.exceptions.ConnectionError from ORM
    '''
    # 
    def __init__(self, uri, message=None):
        Exception.__init__(self, message)
        self.urn = uri
        self.clab_message = 'Unexisting URI. Impossible to connect. (%s)'%(uri)
    def __str__(self):
        return repr(self.clab_message)

class InvalidURI (Exception):
    '''
    Exception indicating an invalid URN received as argument
    The URI provided exists, but it does not correspond to a valid Testbed Controller.
    The URI must be the either the base URI of the REST API of the Testbed Controller
    or a valid URI of retrievable resource of the testbed.
    Encapsulates ValueError exception from ORM
    '''
    # ValueError
    def __init__(self, uri, message=None):
        Exception.__init__(self, message)
        self.urn = uri
        self.clab_message = 'The given URI does not correspond to a valid base URI or resource URI of the Testbed. (%s)'%(uri)
    def __str__(self):
        return repr(self.clab_message)        

class ResourceNotFound (Exception):
    '''
    Exception indicating that the resource requested was not found.
    Encapsulates orm.api.ResponseStatusError
    '''
    def __init__(self, resource, message=None):
        Exception.__init__(self, message)
        self.resource = resource
        self.clab_message = 'The requested resource was not found in the testbed. (%s)'%(resource)
    def __str__(self):
        return repr(self.clab_message)


class OperationFailed (Exception):
    '''
    Exception indicating that the operation requested failed in its execution
    Encapsulates orm.api.ResponseStatusError and uses its message to provide information
    about the failure
    '''
    def __init__(self, op, message=None):
        Exception.__init__(self, message)
        self.op = op
        self.clab_message = 'The requested operation failed: (%s) # DETAILS: %s'%(op, message)
    def __str__(self):
        return repr(self.clab_message)


########################################################################


class InvalidURN (Exception):
    '''
    Exception indicating an invalid URN received as argument
    '''
    def __init__(self, urn, message=None):
        Exception.__init__(self, message)
        self.urn = urn


class OperationNotAllowed (Exception):
    '''
    Exception indicating that the operation requested was not allowed
    '''
    def __init__(self, op, message=None):
        Exception.__init__(self, message)
        self.op = op



class NotAvailableNodes (Exception):
    '''
    Exception indicating that there are no available nodes for the requested slice
    '''
    def __init__(self, slice_uri, message=None):
        Exception.__init__(self, message)
        self.slice_uri = slice_uri



class MalformedRSpec (Exception):
    '''
    Exception indicating a malformed rspec received as argument
    '''
    def __init__(self, rspec, message=None):
        Exception.__init__(self, message)
        self.rspec = rspec




