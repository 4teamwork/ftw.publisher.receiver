def delete_auto_generated_contents(self, event):
    """
    removes all auto created childs from FormFolder
    """

    ids = event.obj.objectIds()
    event.obj.manage_delObjects(ids)

    return
