from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.core.states import DecodeError
from ftw.publisher.core.states import PartialError
from ftw.publisher.receiver import helpers
from ftw.publisher.receiver.decoder import Decoder
from ftw.publisher.receiver.helpers import IS_PLONE_4
from ftw.publisher.receiver.tests import IntegrationTestCase
from ftw.testing import IS_PLONE_5


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

    def test_unserialize_fields(self):
        asset_name = 'basic_folder.json' if IS_PLONE_4 else 'basic_folder_dx.json'
        self.decoder(self.asset(asset_name).text())
        self.grant('Manager')
        folder = create(Builder('folder').titled(u'Foo'))
        helpers.set_uid(folder, self.decoder.data['metadata']['UID'])

        data_adapter_name = u'field_data_adapter' if IS_PLONE_4 else u'dx_field_data_adapter'
        field_data = self.decoder.unserializeFields(
            folder, data_adapter_name)[data_adapter_name]

        if IS_PLONE_5:
            expected = {
                'IAllowDiscussion': {'allow_discussion': None},
                'IDublinCore': {'contributors': (),
                             'creators': (u'test_user_1_',),
                             'description': u'',
                             'effective': None,
                             'expires': None,
                             'language': 'en',
                             'rights': None,
                             'subjects': (),
                             'title': u'A folder'},
                'IExcludeFromNavigation': {'exclude_from_nav': None},
                'INextPreviousToggle': {'nextPreviousEnabled': False},
                'IRelatedItems': {'relatedItems': ['raw', None]},
                'IShortName': {'id': 'a-folder'},
                'plone_0_Folder': {}
            }
        else:
            expected = {
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
            }

        self.assertDictContainsSubset(expected, field_data)
