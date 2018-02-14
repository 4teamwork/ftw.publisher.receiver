from Acquisition import aq_base
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
import plone.uuid


def set_uid(obj, uid):

    if hasattr(aq_base(obj), '_setUID'):
        obj._setUID(uid)
    else:
        setattr(obj, plone.uuid.interfaces.ATTRIBUTE_NAME, uid)
        notify(ObjectAddedEvent(obj))
