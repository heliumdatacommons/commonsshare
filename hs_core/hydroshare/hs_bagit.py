import os
import shutil
import logging

from hs_core.models import Bags

logger = logging.getLogger(__name__)

def delete_files_and_bag(resource):
    """
    delete the resource bag and all resource files.

    Parameters:
    :param resource: the resource to delete the bag and files for.
    :return: none
    """
    istorage = resource.get_irods_storage()

    # delete resource directory first to remove all generated bag-related files for the resource
    if istorage.exists(resource.root_path):
        istorage.delete(resource.root_path)

    if istorage.exists(resource.bag_path):
        istorage.delete(resource.bag_path)

    # TODO: delete this whole mechanism; redundant.
    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()

def create_bag(resource):
    """
        create a zip archive for the resource, only a zip no bdbag

        Parameters:
        :param resource: the resource, consisting of files to create the bdbag.
        :return: a Bag object which points to the newly created bag.
        """

    output_zipname = os.path.join('bags', resource.short_id + '.zip')

    istorage = resource.get_irods_storage()

    istorage.zipup(resource.root_path + "/data", output_zipname)

    # set bag_modified to false for a newly created bag
    path = resource.root_path
    istorage.setAVU(path, "bag_modified", "false")

    # delete if there exists any bags for the resource
    resource.bags.all().delete()

    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b