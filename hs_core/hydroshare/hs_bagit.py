import os
import hashlib
import json
import shutil
import logging

from uuid import uuid4
from mezzanine.conf import settings

from hs_core.models import Bags, ResourceFile
from bdbag import bdbag_api as bdb
from minid_client import minid_client_api as mca
from django_irods.icommands import SessionException


logger = logging.getLogger(__name__)


class HsBagitException(Exception):
    pass


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
        create a bdbag for the resource

        Parameters:
        :param resource: the resource, consisting of files to create the bdbag.
        :return: a Bag object which points to the newly created bag.
        """
    checksums = ['md5', 'sha256']

    tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex, resource.short_id)
    os.makedirs(tmpdir)

    # generate remote-file-mainfest for fetch.txt
    remote_file_manifest_json = get_remote_file_manifest(tmpdir, resource)

    # generate metatdata json for bag-info.txt
    metadata_json = get_metadata_json(resource)

    # create the remote manifest and metadata files
    remote_manifest_file = os.path.join(tmpdir, 'remote-file-manifest.json')
    with open(remote_manifest_file, 'w') as outfile:
        json.dump(remote_file_manifest_json, outfile)

    metadata_file = os.path.join(tmpdir, 'metadata.json')
    with open(metadata_file, 'w') as outfile:
        json.dump(metadata_json, outfile)

    bagdir = os.path.join(tmpdir, "bag")
    os.makedirs(bagdir)

    # make the bdbag and create a zip archive
    bdb.make_bag(bagdir, checksums, False, False, False, None, metadata_file, remote_manifest_file, 'hydroshare/bdbag.json')
    zipfile = bdb.archive_bag(bagdir, "zip")

    # save the zipped bag to iRODS for retrieval upon download request
    istorage = resource.get_irods_storage()
    bag_full_name = 'bags/{res_id}.zip'.format(res_id=resource.short_id)
    irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
    destbagfile = os.path.join(irods_dest_prefix, bag_full_name)

    istorage.saveFile(zipfile, destbagfile, True)

    # set bag_modified to false for a newly created bag
    path = resource.root_path
    istorage.setAVU(path, "bag_modified", "false")

    # delete if there exists any bags for the resource
    resource.bags.all().delete()

    # clean up temp directory
    shutil.rmtree(tmpdir)

    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b

def get_remote_file_manifest(tmpdir, resource):
    data_list = []

    from hs_core.hydroshare import utils

    istorage = resource.get_irods_storage()

    for f in ResourceFile.objects.filter(object_id=resource.id):
        data = {}

        if f.reference_file_path:
            irods_file_name = f.reference_file_path
            srcfile = irods_file_name
            last_sep_pos = irods_file_name.rfind('/')
            ref_file_name = irods_file_name[last_sep_pos+1:]
            fetch_url = '{0}/django_irods/download/{1}'.format(utils.current_site_url(), resource.short_id + irods_file_name)
            checksum = istorage.get_checksum(srcfile)
        else:
            irods_file_name = f.storage_path
            irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
            srcfile = os.path.join(irods_dest_prefix, irods_file_name)
            fetch_url = '{0}/django_irods/download/{1}'.format(utils.current_site_url(), irods_file_name)
            checksum = istorage.checksum(srcfile)

        data['url'] = fetch_url

        if (f.reference_file_path):
            data['length'] = istorage.size(srcfile)
            data['filename'] = ref_file_name
        else:
            data['length'] = f.size
            data['filename'] = f.file_name

        if checksum.startswith('sha'):
            data['sha256'] = checksum[4:]
        elif checksum.startswith('md5'):
            data['md5'] = checksum[4:]

        data_list.append(data)

    return data_list

def get_metadata_json(resource):
    data = {}
    data['BagIt-Profile-Identifier'] = "https://raw.githubusercontent.com/fair-research/bdbag/master/profiles/bdbag-profile.json"
    data['External-Description'] = "CommonsShare BDBag for resource " + resource.short_id
    data['Arbitrary-Metadata-Field'] = "TBD Arbitrary metadata field"

    return data
