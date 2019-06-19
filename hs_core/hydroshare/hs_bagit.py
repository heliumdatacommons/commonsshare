import os
import logging
import shutil

from django.conf import settings

from hs_core.models import Bags

logger = logging.getLogger(__name__)

def delete_files_and_bag(resource):
    """
    delete the resource bag and all resource files.

    Parameters:
    :param resource: the resource to delete the bag and files for.
    :return: none
    """
    if settings.USE_IRODS:
        istorage = resource.get_irods_storage()
        # delete resource directory first to remove all generated bag-related files for the resource
        if istorage.exists(resource.root_path):
            istorage.delete(resource.root_path)

        if istorage.exists(resource.bag_path):
            istorage.delete(resource.bag_path)
    else:
        istorage = resource.get_file_system_storage()
        location = istorage.location
        shutil.rmtree(os.path.join(location, resource.short_id), ignore_errors=True)
        try:
            os.remove(os.path.join(location, 'bags', resource.short_id + '.zip'))
        except OSError:
            pass

    # TODO: delete this whole mechanism; redundant.
    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()

def create_bag(resource):
    """
        create a zip archive for the resource, only a zip no bdbag

        Parameters:
        :param resource: the resource, consisting of files to create the bdbag.
        :return: a Bag object which points to the newly created bag, and zipped bag path
        """

    if settings.USE_IRODS:
        istorage = resource.get_irods_storage()
        output_zipname = os.path.join('bags', resource.short_id + '.zip')
        istorage.zipup(resource.root_path + "/data", output_zipname)

        # set bag_modified to false for a newly created bag
        path = resource.root_path
        istorage.setAVU(path, "bag_modified", "false")
    else:
        istorage = resource.get_file_system_storage()
        location = istorage.location
        output_zip_basename = os.path.join(location, 'bags', resource.short_id)
        input_path = os.path.join(location, resource.short_id)
        shutil.make_archive(output_zip_basename, 'zip', input_path)
        output_zipname = output_zip_basename + '.zip'

    # delete if there exists any bags for the resource
    resource.bags.all().delete()

    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b, output_zipname
