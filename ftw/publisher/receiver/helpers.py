from Acquisition import aq_base
from Products.CMFPlone.utils import getFSVersionTuple
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
import plone.uuid


IS_PLONE_4 = (4,) <= getFSVersionTuple() < (5,)


def set_uid(obj, uid):

    if hasattr(aq_base(obj), '_setUID'):
        obj._setUID(uid)
    else:
        setattr(obj, plone.uuid.interfaces.ATTRIBUTE_NAME, uid)
        notify(ObjectAddedEvent(obj))
