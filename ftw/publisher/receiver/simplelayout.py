from ftw.simplelayout.configuration import flattened_block_uids
from ftw.simplelayout.interfaces import IPageConfiguration
from ftw.simplelayout.interfaces import ISimplelayoutBlock
from operator import methodcaller
from plone.uuid.interfaces import IUUID


def remove_deleted_blocks_after_update(page, event):
    """When updating a ftw.simplelayout page / container, remove all blocks
    which are not in the page state.
    When deleting blocks, no detele-jobs are triggered, therefore we need to remove
    the blocks when updating the page.
    """

    block_uids_in_config = flattened_block_uids(IPageConfiguration(page).load())
    blocks_to_delete = filter(lambda block: IUUID(block) not in block_uids_in_config,
                              filter(ISimplelayoutBlock.providedBy,
                                     page.objectValues()))
    page.manage_delObjects(map(methodcaller('getId'), blocks_to_delete))
