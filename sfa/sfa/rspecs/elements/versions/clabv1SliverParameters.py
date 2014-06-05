'''
Created on Jun 4, 2014

@author: gerard
'''
from sfa.rspecs.elements.element import Element

class Clabv1SliverParameters(Element):
    fields = [
        'template',
        'overlay',
        'sliver_interfaces',
    ]


class Clabv1Template(Element):
    fields = [
        'name',
        'id',
    ]


class Clabv1Overlay(Element):
    fields = [
        'file',
        'uri',
        'sha256',
    ]


class Clabv1NetworkInterface(Element):
    fields = [
        'name',
        'type',
        'nr',
    ]