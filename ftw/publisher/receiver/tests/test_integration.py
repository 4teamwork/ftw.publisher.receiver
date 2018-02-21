from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.receiver import helpers
from ftw.publisher.receiver.helpers import IS_PLONE_4
from ftw.publisher.receiver.tests import IntegrationTestCase
from plone.uuid.interfaces import IUUID


class TestDecoder(IntegrationTestCase):

    def test_receiving_image_push_creates_object(self):
        self.assertNotIn('bar.jpg', self.portal.objectIds(),
                         'Precondition: image should not yet exist.')
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectCreatedState')
        self.assertIn('bar.jpg', self.portal.objectIds(),
                      'Image should have been created.')

        image = self.portal.get('bar.jpg')
        self.assertEquals('Image', image.portal_type)
        self.assertEquals('02ef694164310bca909d963f515e376d', IUUID(image))

    def test_receiving_image_push_updates_object(self):
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectCreatedState')
        image = self.portal.get('bar.jpg')
        image.setTitle('Some Title')
        self.assertEquals('Some Title', image.Title())
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectUpdatedState')
        self.assertEquals('logo.jpg', image.Title())

    def test_receiving_image_move_moves_object(self):
        self.grant('Manager')
        image = create(Builder('image').titled(u'bar.jpg'))
        helpers.set_uid(image, '02ef694164310bca909d963f515e376d')
        image.reindexObject()
        self.assertEquals('/plone/bar.jpg', '/'.join(image.getPhysicalPath()))
        self.receive('move_image.json', expected_result='ObjectMovedState')
        self.assertEquals('/plone/bar2.jpg', '/'.join(image.getPhysicalPath()))
        self.assertEquals('logo.jpg', image.Title())

    def test_receive_fails_when_other_object_exists_at_path(self):
        self.grant('Manager')
        # Create image at same path but with different UID
        create(Builder('image').titled(u'bar.jpg'))
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='UnexpectedError')

    def test_receiving_object_existing_at_different_path_moves_object(self):
        self.grant('Manager')
        image = create(Builder('image').titled(u'something.jpg'))
        helpers.set_uid(image, '02ef694164310bca909d963f515e376d')
        image.reindexObject()
        self.assertEquals('/plone/something.jpg', '/'.join(image.getPhysicalPath()))
        self.assertEquals('something.jpg', image.Title())
        asset_name = 'image.json' if IS_PLONE_4 else 'image_dx.json'
        self.receive(asset_name, expected_result='ObjectUpdatedState')
        self.assertEquals('/plone/bar.jpg', '/'.join(image.getPhysicalPath()))
        self.assertEquals('logo.jpg', image.Title())
