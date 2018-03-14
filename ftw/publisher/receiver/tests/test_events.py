from ftw.publisher.receiver.helpers import IS_PLONE_4
from ftw.publisher.receiver.interfaces import IAfterCreatedEvent
from ftw.publisher.receiver.interfaces import IAfterUpdatedEvent
from ftw.publisher.receiver.tests import IntegrationTestCase
from zope.component import getSiteManager


class RecordingSubscriber(object):

    def __init__(self):
        self.calls = []

    def __call__(self, event):
        self.calls.append(event)

    @classmethod
    def for_event(klass, event_interface):
        subscriber = klass()
        getSiteManager().registerHandler(subscriber, [event_interface])
        return subscriber


class TestEvents(IntegrationTestCase):

    def test_create_event_fired(self):
        created_subscriber = RecordingSubscriber.for_event(IAfterCreatedEvent)
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectCreatedState')
        event, = created_subscriber.calls
        self.assertEquals(self.portal['bar.jpg'], event.obj)

    def test_update_event_fired(self):
        updated_subscriber = RecordingSubscriber.for_event(IAfterUpdatedEvent)
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectCreatedState')
        self.receive(asset_name, expected_result='ObjectUpdatedState')
        event, = updated_subscriber.calls
        self.assertEquals(self.portal['bar.jpg'], event.obj)
