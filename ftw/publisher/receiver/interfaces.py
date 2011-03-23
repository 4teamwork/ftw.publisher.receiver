from zope.component.interfaces import IObjectEvent


class IAfterCreatedEvent(IObjectEvent):
    """
    Event gets fired, after object is created on the remote site
    """


class IAfterUpdatedEvent(IObjectEvent):
    """
    Event gets fired, after object is created on the remote site
    """
