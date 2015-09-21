from ftw.builder import Builder
from ftw.builder import create
from ftw.publisher.receiver.events import AfterUpdatedEvent
from ftw.publisher.receiver.tests import IntegrationTestCase
from ftw.simplelayout.configuration import columns_in_config
from ftw.simplelayout.configuration import flattened_block_uids
from ftw.simplelayout.interfaces import IPageConfiguration
from ftw.testing import staticuid
from zope.event import notify


class TestSimplelayout(IntegrationTestCase):

    @staticuid('staticuid')
    def test_removes_blocks_not_in_pagestate_after_updating(self):
        page = create(Builder('sl content page')
                      .with_blocks(Builder('sl textblock').titled(u'Foo'),
                                   Builder('sl textblock').titled(u'Bar'),
                                   Builder('sl textblock').titled(u'Baz')))
        create(Builder('sl content page').within(page).titled(u'Subpage'))
        self.assertEquals(['foo', 'bar', 'baz', 'subpage'], page.objectIds())

        config = IPageConfiguration(page).load()
        blocks = columns_in_config(config)[0]['blocks']
        self.assertEquals(3, len(blocks), 'Expected exactly 3 blocks in config.')
        del columns_in_config(config)[0]['blocks'][1]
        IPageConfiguration(page).store(config)

        notify(AfterUpdatedEvent(page))
        self.assertEquals(['foo', 'baz', 'subpage'], page.objectIds())
