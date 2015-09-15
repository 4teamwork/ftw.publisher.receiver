from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.core.states import DecodeError
from ftw.publisher.core.states import PartialError
from ftw.publisher.receiver.decoder import Decoder
from ftw.publisher.receiver.tests import IntegrationTestCase


class TestDecoder(IntegrationTestCase):

    def setUp(self):
        super(TestDecoder, self).setUp()
        self.decoder = Decoder(self.portal)

    def test_decodeJson_raises_decode_error_when_input_invalid(self):
        with self.assertRaises(DecodeError) as cm:
            self.decoder.decodeJson('erroneous data')

        self.assertEquals('No JSON object could be decoded',
                          str(cm.exception))

    def test_decodes_prefixed_strings(self):
        """When the sender encodes to JSON, it prefixes all strings with
        the encoding, since some tools and components in plone need to
        utf8-encoded strings, others need unicode, etc.
        """
        result = self.decoder.decodeJson('["unicode:foo", "utf8:bar"]')
        self.assertEquals([[u'foo', 'bar'], [unicode, str]],
                          [result, map(type, result)])

    def test_validates_that_metadata_is_present(self):
        self.decoder.data = {}
        with self.assertRaises(PartialError) as cm:
            self.decoder.validate()

        self.assertEquals('Missing "metadata"', str(cm.exception))

    def test_validates_that_required_metadata_is_present(self):
        self.decoder.data = dict(metadata={
            'UID': 'foobar123',
            'id': 'foo',
            'portal_type': 'Folder',
            'action': 'push',
            'physicalPath': '/platform/foo',
            'sibling_positions': []
        })
        self.decoder.validate()

        del self.decoder.data['metadata']['portal_type']
        with self.assertRaises(PartialError) as cm:
            self.decoder.validate()

        self.assertEquals('Missing "metadata.portal_type"',
                          str(cm.exception))

    def test_load_schema_from_object(self):
        self.decoder(self.asset('basic_folder.json').text())
        self.grant('Manager')
        folder = create(Builder('folder').titled('Foo'))
        folder._setUID(self.decoder.data['metadata']['UID'])

        schema = self.decoder.getSchema(folder)
        self.assertTrue(schema)

    def test_unserialize_fields(self):
        self.decoder(self.asset('basic_folder.json').text())
        self.grant('Manager')
        folder = create(Builder('folder').titled('Foo'))
        folder._setUID(self.decoder.data['metadata']['UID'])

        field_data = self.decoder.unserializeFields(
            folder, u'field_data_adapter')[u'field_data_adapter']

        self.assertDictContainsSubset(
            {
                'allowDiscussion': False,
                'contributors': [],
                'creation_date': '2011/03/23 14:26:54.592 GMT+1',
                'creators': ['test_user_1_'],
                'description': '',
                'effectiveDate': None,
                'excludeFromNav': False,
                'expirationDate': None,
                'id': 'foo',
                'language': '',
                'location': '',
                'modification_date': '2011/03/23 14:26:54.615 GMT+1',
                'nextPreviousEnabled': False,
                'relatedItems': [],
                'rights': '',
                'subject': [],
                'title': 'Foo',
            },
            field_data)

    def test_site_root_schema_is_None(self):
        # The site root hase no schema.
        # Therefore getting the schema schould return None
        # and should not crash.

        self.decoder(self.asset('plonesite.json').text())
        self.assertEquals(None, self.decoder.getSchema(self.portal))
