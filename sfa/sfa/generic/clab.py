'''
Created on Mar 5, 2014

@author: gerard
'''
from sfa.generic import Generic


class clab (Generic):

    # the importer class
    def importer_class (self):
        import sfa.importer.clabimporter
        return sfa.importer.clabimporter.ClabImporter

    # use the standard api class
    def api_class (self):
        import sfa.server.sfaapi
        return sfa.server.sfaapi.SfaApi

    # the manager classes for the server-side services
    def registry_manager_class (self) :
        import sfa.managers.registry_manager
        return sfa.managers.registry_manager.RegistryManager
    def slicemgr_manager_class (self) :
        import sfa.managers.slice_manager
        return sfa.managers.slice_manager.SliceManager
    def aggregate_manager_class (self) :
        import sfa.managers.aggregate_manager
        return sfa.managers.aggregate_manager.AggregateManager

    # driver class for server-side services, talk to the whole testbed
    def driver_class (self):
        import sfa.clab.clab_driver
        return sfa.clab.clab_driver.ClabDriver

    # for the component mode, to be run on board planetlab nodes
    # manager class
    def component_manager_class (self):
        return None
    # driver_class
    def component_driver_class (self):
        return None