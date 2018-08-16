import json
from hs_core import hydroshare
from django.core.urlresolvers import reverse
from hs_core.views import serializers
from rest_framework.exceptions import ValidationError #  NotAuthenticated, PermissionDenied, NotFound

def resourceToBundle(r):
    """ the purpose of this method is to convert a resource object into an dos api '
    bundle object. """
    site_url = hydroshare.utils.current_site_url()
    bag_url = site_url + r.bag_url
    science_metadata_url = site_url + reverse('get_update_science_metadata', args=[r.short_id])
    resource_map_url = site_url + reverse('get_resource_map', args=[r.short_id])
    resource_url = site_url + r.get_absolute_url()
    coverages = [{"type": v['type'], "value": json.loads(v['_value'])}
                    for v in r.metadata.coverages.values()]
    resource_list_item = serializers.ResourceListItem(resource_type=r.resource_type,
                                                        resource_id=r.short_id,
                                                        resource_title=r.metadata.title.value,
                                                        creator=r.first_creator.name,
                                                        public=r.raccess.public,
                                                        discoverable=r.raccess.discoverable,
                                                        shareable=r.raccess.shareable,
                                                        immutable=r.raccess.immutable,
                                                        published=r.raccess.published,
                                                        date_created=r.created,
                                                        date_last_updated=r.updated,
                                                        bag_url=bag_url,
                                                        coverages=coverages,
                                                        science_metadata_url=science_metadata_url,
                                                        resource_map_url=resource_map_url,
                                                        resource_url=resource_url)
    return resource_list_item


def get_databundle_list(request):

    filtered_res_list = []

    for r in hydroshare.get_resource_list(**{"public": True}):
        resource_list_item = resourceToResourceListItem(r)
        return resource_list_item
        # filtered_res_list.append(resource_list_item)

    return filtered_res_list