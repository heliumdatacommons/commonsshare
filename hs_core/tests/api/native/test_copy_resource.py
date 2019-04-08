import os
import tempfile
import shutil

from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.hydroshare import utils
from hs_access_control.models import PrivilegeCodes


class TestCopyResource(TestCase):
    def setUp(self):
        super(TestCopyResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='CommonsShare Author')

        # create a user who is the owner of the resource to be copied
        self.owner = hydroshare.create_account(
            'owner@gmail.edu',
            username='owner',
            first_name='owner_firstname',
            last_name='owner_lastname',
            superuser=False,
            groups=[]
        )

        # create a user who is NOT the owner of the resource to be copied
        self.nonowner = hydroshare.create_account(
            'nonowner@gmail.com',
            username='nonowner',
            first_name='nonowner_firstname',
            last_name='nonowner_lastname',
            superuser=False,
            groups=[]
        )

        # create a generic resource
        self.res_generic = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource'
        )

        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file2 = open('test2.txt', 'w')
        test_file2.write("Test text file in test2.txt")
        test_file2.close()
        self.test_file1 = open('test1.txt', 'r')
        self.test_file2 = open('test2.txt', 'r')

        hydroshare.add_resource_files(self.res_generic, self.test_file1, self.test_file2)

        # create a generic empty resource with one license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons Attribution-NoDerivs CC ' \
                    'BY-ND.'
        url = 'http://creativecommons.org/licenses/by-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_generic_lic_nd = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource',
            metadata=metadata
        )

        # create a generic empty resource with another license that prohibits derivation
        statement = 'This resource is shared under the Creative Commons ' \
                    'Attribution-NoCommercial-NoDerivs CC BY-NC-ND.'
        url = 'http://creativecommons.org/licenses/by-nc-nd/4.0/'
        metadata = []
        metadata.append({'rights': {'statement': statement, 'url': url}})
        self.res_generic_lic_nc_nd = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource',
            metadata=metadata
        )


    def tearDown(self):
        super(TestCopyResource, self).tearDown()
        if self.res_generic:
            self.res_generic.delete()
        if self.res_generic_lic_nd:
            self.res_generic_lic_nd.delete()
        if self.res_generic_lic_nc_nd:
            self.res_generic_lic_nc_nd.delete()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_copy_generic_resource(self):
        # ensure a nonowner who does not have permission to view a resource cannot copy it
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic.short_id,
                                             self.nonowner,
                                             action='copy')
        # ensure resource cannot be copied if the license does not allow derivation by a non-owner
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic_lic_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.res_generic_lic_nc_nd.short_id,
                                             self.nonowner,
                                             action='copy')

        # add key/value metadata to original resource
        self.res_generic.extra_metadata = {'variable': 'temp', 'units': 'deg F'}
        self.res_generic.save()

        # give nonowner view privilege so nonowner can create a new copy of this resource
        self.owner.uaccess.share_resource_with_user(self.res_generic, self.nonowner,
                                                    PrivilegeCodes.VIEW)
        new_res_generic = hydroshare.create_empty_resource(self.res_generic.short_id,
                                                           self.nonowner,
                                                           action='copy')
        # test to make sure the new copied empty resource has no content files
        self.assertEqual(new_res_generic.files.all().count(), 0)

        new_res_generic = hydroshare.copy_resource(self.res_generic, new_res_generic)

        # test the new copied resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res_generic, GenericResource))

        # test the new copied resource has the correct content file with correct path copied over
        self.assertEqual(new_res_generic.files.all().count(), 2)
        # add each file of resource to list
        new_res_file_list = []
        for f in new_res_generic.files.all():
            new_res_file_list.append(f.resource_file.name)
        for f in self.res_generic.files.all():
            ori_res_no_id_file_path = f.resource_file.name[len(self.res_generic.short_id):]
            new_res_file_path = new_res_generic.short_id + ori_res_no_id_file_path
            self.assertIn(new_res_file_path, new_res_file_list,
                          msg='resource content path is not created correctly '
                              'for new copied resource')

        # test key/value metadata copied over
        self.assertEqual(new_res_generic.extra_metadata, self.res_generic.extra_metadata)
        # test science metadata elements are copied from the original resource to the new copied
        # resource
        self.assertEqual(new_res_generic.metadata.title.value,
                         self.res_generic.metadata.title.value,
                         msg='metadata title is not copied over to the new copied resource')
        self.assertEqual(new_res_generic.creator, self.nonowner,
                         msg='creator is not copied over to the new copied resource')

        # test to make sure a new unique identifier has been created for the new copied resource
        self.assertIsNotNone(
            new_res_generic.short_id,
            msg='Unique identifier has not been created for new copied resource.')
        self.assertNotEqual(new_res_generic.short_id, self.res_generic.short_id)

        # test to make sure the new copied resource has the correct identifier
        self.assertEqual(new_res_generic.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier',
                      [id.name for id in new_res_generic.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new copied resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                         new_res_generic.short_id)
        self.assertIn(id_url, [id.url for id in new_res_generic.metadata.identifiers.all()],
                      msg="Identifier url was not found for new copied resource.")

        # test to make sure the new copied resource is linked with the original resource via
        # isDerivedFrom Source metadata element
        self.assertGreater(new_res_generic.metadata.sources.all().count(), 0,
                           msg="New copied resource does not has source element.")

        derived_from_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(),
                                                     self.res_generic.short_id)
        self.assertIn(derived_from_value,
                      [src.derived_from for src in new_res_generic.metadata.sources.all()],
                      msg="The original resource identifier is not set in isDerivedFrom Source "
                          "metadata element of the new copied resource")
        # make sure to clean up resource so that irods storage can be cleaned up
        if new_res_generic:
            new_res_generic.delete()