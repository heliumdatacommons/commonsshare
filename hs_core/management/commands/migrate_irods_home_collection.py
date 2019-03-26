"""
Migrate data from default /zone/home/proxy_irods_user to /zone/data/proxy_irods_user so that
the proxy_irods_user can read each individual user's home collection and create a resource using
files from those collections
"""
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException


def copy_data_and_set_access_control(source_path='', res=None):
    """ copy data for res_id and set access control accordingly """

    if not source_path or not res:
        print "source_path or res being passed in cannot be empty"
        return

    istorage = IrodsStorage()  # local only
    source_path = os.path.join(source_path, res.short_id, 'data')
    istorage.copyFiles(source_path, res.root_path)
    # set access control accordingly depending on whether the resource is public
    is_public = res.raccess.public
    if is_public:  # can't be public without being discoverable
        res.set_irods_access_control(user_or_group_name='public', perm='read')
    else:
        res.set_irods_access_control(user_or_group_name='public', perm='null')

    # give all owners read access
    for owner in res.raccess.owners.all():
        try:
            res.set_irods_access_control(user_or_group_name=owner.username, perm='read')
        except SessionException as ex:
            print('Cannot give owner ' + owner.username + ' read permission to resource ' +
                  res.short_id + ': ' + ex.stderr)
            continue
    # give all editors read access
    for editor in res.raccess.edit_users.all():
        try:
            res.set_irods_access_control(user_or_group_name=editor.username, perm='read')
        except SessionException as ex:
            print('Cannot give editor ' + editor.username + ' read permission to resource ' +
                  res.short_id + ': ' + ex.stderr)
            continue
    # give all viewers read access
    for viewer in res.raccess.view_users.all():
        try:
            res.set_irods_access_control(user_or_group_name=viewer.username, perm='read')
        except SessionException as ex:
            print('Cannot give viewer ' + viewer.username + ' read permission to resource ' +
                  res.short_id + ': ' + ex.stderr)
            continue
    # give all group members read access
    for g in res.raccess.edit_groups.all():
        for u in g.gaccess.members:
            try:
                res.set_irods_access_control(user_or_group_name=u.username)
            except SessionException as ex:
                print('Cannot give group member ' + u.username + ' read permission to resource ' +
                      res.short_id + ': ' + ex.stderr)
                continue
    for g in res.raccess.view_groups.all():
        for u in g.gaccess.members:
            try:
                res.set_irods_access_control(user_or_group_name=u.username)
            except SessionException as ex:
                print('Cannot give group member ' + u.username + ' read permission to resource ' +
                      res.short_id + ': ' + ex.stderr)
                continue


class Command(BaseCommand):
    help = "Migrate data from default /zone/home/proxy_irods_user to /zone/data/proxy_irods_user."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)


    def handle(self, *args, **options):
        source_path = '/' + settings.IRODS_ZONE + '/home/' + settings.IRODS_USERNAME
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    res = get_resource_by_shortkey(rid, or_404=False)
                except BaseResource.DoesNotExist:
                    print('resource ' + rid + ' does not exist in Django DB')
                copy_data_and_set_access_control(source_path, res)
        else:  # check all resources
            for r in BaseResource.objects.all():
                copy_data_and_set_access_control(source_path, r)
