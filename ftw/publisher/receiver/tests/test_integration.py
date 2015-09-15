from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.receiver.tests import IntegrationTestCase
from plone.uuid.interfaces import IUUID


class TestDecoder(IntegrationTestCase):

    def setUp(self):
        super(TestDecoder, self).setUp()
        self.grant('Manager')

    def test_receiving_image_push_creates_object(self):
        self.assertNotIn('bar.jpg', self.portal.objectIds(),
                         'Precondition: image should not yet exist.')
        self.receive('image.json', expected_result='ObjectCreatedState')
        self.assertIn('bar.jpg', self.portal.objectIds(),
                      'Image should have been created.')

        image = self.portal.get('bar.jpg')
        self.assertEquals('Image', image.portal_type)
        self.assertEquals('02ef694164310bca909d963f515e376d', IUUID(image))

    def test_receiving_image_push_updates_object(self):
        self.receive('image.json', expected_result='ObjectCreatedState')
        image = self.portal.get('bar.jpg')
        image.setTitle('Some Title')
        self.assertEquals('Some Title', image.Title())
        self.receive('image.json', expected_result='ObjectUpdatedState')
        self.assertEquals('logo.jpg', image.Title())

    def test_receiving_image_move_moves_object(self):
        image = create(Builder('image').titled('bar.jpg'))
        image._setUID('02ef694164310bca909d963f515e376d')
        image.reindexObject()
        self.assertEquals('/plone/bar.jpg', '/'.join(image.getPhysicalPath()))
        self.receive('move_image.json', expected_result='ObjectMovedState')
        self.assertEquals('/plone/bar2.jpg', '/'.join(image.getPhysicalPath()))
        self.assertEquals('logo.jpg', image.Title())

    def receive(self, asset_filename, expected_result):
        self.request.set('jsondata', self.asset(asset_filename).text())
        response = self.portal.restrictedTraverse('publisher.receive')()
        self.assertTrue(
            response.startswith(expected_result),
            'Unexpected receive result, expected: {}\n Got: {}'.format(
                expected_result,
                response))
