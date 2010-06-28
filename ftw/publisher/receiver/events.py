from zope.component.interfaces import ObjectEvent
from zope import interface
from interfaces import IAfterCreatedEvent, IAfterUpdatedEvent


class AfterCreatedEvent(ObjectEvent):
    interface.implements(IAfterCreatedEvent)

    def __init__(self, context):
        ObjectEvent.__init__(self, context)
        self.obj = context
    
    
class AfterUpdatedEvent(ObjectEvent):
    interface.implements(IAfterUpdatedEvent)

    def __init__(self, context):
        ObjectEvent.__init__(self, context)
        self.obj = context