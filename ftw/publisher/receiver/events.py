from AccessControl.SecurityInfo import ClassSecurityInformation
from interfaces import IAfterCreatedEvent, IAfterUpdatedEvent
from zope import interface
from zope.component.interfaces import ObjectEvent


class AfterCreatedEvent(ObjectEvent):
    interface.implements(IAfterCreatedEvent)
    security = ClassSecurityInformation()

    def __init__(self, context):
        ObjectEvent.__init__(self, context)
        self.obj = context


class AfterUpdatedEvent(ObjectEvent):
    interface.implements(IAfterUpdatedEvent)
    security = ClassSecurityInformation()

    def __init__(self, context):
        ObjectEvent.__init__(self, context)
        self.obj = context
