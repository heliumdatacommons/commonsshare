"""Define search indexes for hs_core module."""

from haystack import indexes
from hs_core.models import BaseResource
from hs_geographic_feature_resource.models import GeographicFeatureMetaData
from hs_app_netCDF.models import NetcdfMetaData
from ref_ts.models import RefTSMetadata
from hs_app_timeseries.models import TimeSeriesMetaData
from django.db.models import Q
from datetime import datetime
from nameparser import HumanName


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    """Define base class for resource indexes."""

    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    minid = indexes.CharField(model_attr='minid', null=True)
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(faceted=True)
    author_normalized = indexes.CharField(faceted=True)
    author_description = indexes.CharField(indexed=False)
    title = indexes.CharField(faceted=True)
    abstract = indexes.CharField()
    creators = indexes.MultiValueField(faceted=True)
    contributors = indexes.MultiValueField()
    subjects = indexes.MultiValueField(faceted=True)
    public = indexes.BooleanField(faceted=True)
    discoverable = indexes.BooleanField(faceted=True)
    published = indexes.BooleanField(faceted=True)

    extra_metadata = indexes.CharField()

    # TODO: We might need more information than a bool in the future
    is_replaced_by = indexes.BooleanField()
    created = indexes.DateTimeField(model_attr='created', faceted=True)
    modified = indexes.DateTimeField(model_attr='updated', faceted=True)
    organizations = indexes.MultiValueField(faceted=True)
    author_emails = indexes.MultiValueField()
    publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    coverages = indexes.MultiValueField()
    coverage_types = indexes.MultiValueField()
    coverage_start_date = indexes.DateField()
    coverage_end_date = indexes.DateField()
    formats = indexes.MultiValueField()
    identifiers = indexes.MultiValueField()
    language = indexes.CharField(faceted=True)
    sources = indexes.MultiValueField()
    relations = indexes.MultiValueField()
    resource_type = indexes.CharField(faceted=True)
    comments = indexes.MultiValueField()
    comments_count = indexes.IntegerField(faceted=True)
    owners_logins = indexes.MultiValueField(faceted=True)
    owners_names = indexes.MultiValueField(faceted=True)
    owners_count = indexes.IntegerField(faceted=True)
    viewers_logins = indexes.MultiValueField(faceted=True)
    viewers_names = indexes.MultiValueField(faceted=True)
    viewers_count = indexes.IntegerField(faceted=True)
    editors_logins = indexes.MultiValueField(faceted=True)
    editors_names = indexes.MultiValueField(faceted=True)
    editors_count = indexes.IntegerField(faceted=True)
    absolute_url = indexes.CharField(indexed=False)

    # ontology index ids for semantic search
    ontology_id = indexes.MultiValueField()

    def get_model(self):
        """Return BaseResource model."""
        return BaseResource

    def index_queryset(self, using=None):
        """Return queryset including discoverable and public resources."""
        return self.get_model().objects.filter(Q(raccess__discoverable=True) |
                                               Q(raccess__public=True))

    def prepare_title(self, obj):
        """Return metadata title if exists, otherwise return none."""
        if hasattr(obj, 'metadata') and obj.metadata.title.value is not None:
            return obj.metadata.title.value.lstrip()
        else:
            return 'none'

    def prepare_abstract(self, obj):
        """Return metadata abstract if exists, otherwise return none."""
        if hasattr(obj, 'metadata') and obj.metadata.description is not None and \
                obj.metadata.description.abstract is not None:
            return obj.metadata.description.abstract
        else:
            return 'none'

    def prepare_extra_metadata(self, obj):
        """Return extra_metadata values if exists, otherwise return none."""
        if hasattr(obj, 'extra_metadata') and not obj.extra_metadata:
            extra_md_list = []
            sep = ' ; '
            for k, v in obj.extra_metadata.items():
                extra_md_list.append(k + sep + v)
            return sep.join(extra_md_list)
        else:
            return 'none'

    def prepare_author(self, obj):
        """Return metadata author if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.name is not None:
                return first_creator.name.lstrip()
            else:
                return 'none'
        else:
            return 'none'

    def prepare_author_normalized(self, obj):
        """Return metadata author if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.name is not None:
                nameparts = HumanName(first_creator.name.lstrip())
                normalized = nameparts.last
                if nameparts.suffix:
                    normalized = normalized + ' ' + nameparts.suffix
                normalized = normalized + ','
                if nameparts.title:
                    normalized = normalized + ' ' + nameparts.title
                if nameparts.first:
                    normalized = normalized + ' ' + nameparts.first
                if nameparts.middle:
                    normalized = ' ' + normalized + ' ' + nameparts.middle
                return normalized
            else:
                return 'none'
        else:
            return 'none'

    # stored, unindexed field
    def prepare_author_description(self, obj):
        """Return metadata author description if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.description is not None:
                return first_creator.description
            else:
                return 'none'
        else:
            return 'none'

    def prepare_creators(self, obj):
        """Return metadata creators if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [creator.name for creator in obj.metadata.creators.all()
                    .exclude(name__isnull=True)]
        else:
            return []

    def prepare_contributors(self, obj):
        """Return metadata contributors if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [contributor.name for contributor in obj.metadata.contributors.all()
                    .exclude(name__isnull=True)]
        else:
            return []

    def prepare_subjects(self, obj):
        """Return metadata subjects if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [subject.value for subject in obj.metadata.subjects.all()
                    .exclude(value__isnull=True)]
        else:
            return []

    def prepare_organizations(self, obj):
        """Return metadata organizations if exists, otherwise return empty array."""
        organizations = []
        none = False  # only enter one value "none"
        if hasattr(obj, 'metadata'):
            for creator in obj.metadata.creators.all():
                if(creator.organization is not None):
                    organizations.append(creator.organization)
                else:
                    if not none:
                        none = True
                        organizations.append('none')
        return organizations

    def prepare_publisher(self, obj):
        """Return metadata publisher if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            publisher = obj.metadata.publisher
            if publisher is not None:
                return publisher
            else:
                return 'none'
        else:
            return 'none'

    def prepare_author_emails(self, obj):
        """Return metadata emails if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [creator.email for creator in obj.metadata.creators.all()
                    .exclude(email__isnull=True)]
        else:
            return []

    def prepare_discoverable(self, obj):
        """Return resource discoverability if exists, otherwise return False."""
        if hasattr(obj, 'raccess'):
            if obj.raccess.public or obj.raccess.discoverable:
                return True
            else:
                return False
        else:
            return False

    def prepare_public(self, obj):
        """Return resource access if exists, otherwise return False."""
        if hasattr(obj, 'raccess'):
            if obj.raccess.public:
                return True
            else:
                return False
        else:
            return False

    def prepare_published(self, obj):
        """Return resource published status if exists, otherwise return False."""
        if hasattr(obj, 'raccess'):
            if obj.raccess.published:
                return True
            else:
                return False
        else:
            return False

    def prepare_is_replaced_by(self, obj):
        """Return 'isReplacedBy' attribute if exists, otherwise return False."""
        if hasattr(obj, 'metadata'):
            return obj.metadata.relations.all().filter(type='isReplacedBy').exists()
        else:
            return False

    def prepare_coverages(self, obj):
        """Return resource coverage if exists, otherwise return empty array."""
        # TODO: reject empty coverages
        if hasattr(obj, 'metadata'):
            return [coverage._value for coverage in obj.metadata.coverages.all()]
        else:
            return []

    def prepare_coverage_types(self, obj):
        """Return resource coverage types if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [coverage.type for coverage in obj.metadata.coverages.all()]
        else:
            return []

    # TODO: time coverages do not specify timezone, and timezone support is active.
    def prepare_coverage_start_date(self, obj):
        """Return resource coverage start date if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period':
                    clean_date = coverage.value["start"][:10]
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        start_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    else:
                        parsed_date = clean_date.split("-")
                        start_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
                    return start_date_object
        else:
            return 'none'

    def prepare_coverage_end_date(self, obj):
        """Return resource coverage end date if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period' and 'end' in coverage.value:
                    clean_date = coverage.value["end"][:10]
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        end_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    else:
                        parsed_date = clean_date.split("-")
                        end_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    end_date_object = datetime.strptime(end_date, '%Y-%m-%d')
                    return end_date_object
        else:
            return 'none'

    def prepare_formats(self, obj):
        """Return metadata formats if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [format.value for format in obj.metadata.formats.all()]
        else:
            return []

    def prepare_identifiers(self, obj):
        """Return metadata identifiers if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [identifier.name for identifier in obj.metadata.identifiers.all()]
        else:
            return []

    def prepare_language(self, obj):
        """Return resource language if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            return obj.metadata.language.code
        else:
            return 'none'

    def prepare_sources(self, obj):
        """Return resource sources if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [source.derived_from for source in obj.metadata.sources.all()]
        else:
            return []

    def prepare_relations(self, obj):
        """Return resource relations if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [relation.value for relation in obj.metadata.relations.all()]
        else:
            return []

    def prepare_resource_type(self, obj):
        """Return verbose_name attribute of obj argument."""
        return obj.verbose_name

    def prepare_comments(self, obj):
        """Return list of all comments on resource."""
        return [comment.comment for comment in obj.comments.all()]

    def prepare_comments_count(self, obj):
        """Return count of resource comments."""
        return obj.comments_count

    def prepare_owners_logins(self, obj):
        """Return list of usernames that have ownership access to resource."""
        if hasattr(obj, 'raccess'):
            return [owner.username for owner in obj.raccess.owners.all()]
        else:
            return []

    def prepare_owners_names(self, obj):
        """Return list of names of resource owners."""
        names = []
        if hasattr(obj, 'raccess'):
            for owner in obj.raccess.owners.all():
                name = owner.first_name + ' ' + owner.last_name
                names.append(name)
        return names

    def prepare_owners_count(self, obj):
        """Return count of resource owners if 'raccess' attribute exists, othrerwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.owners.all().count()
        else:
            return 0

    def prepare_viewers_logins(self, obj):
        """Return usernames of users that can view resource, otherwise return empty array."""
        if hasattr(obj, 'raccess'):
            return [viewer.username for viewer in obj.raccess.view_users.all()]
        else:
            return []

    def prepare_viewers_names(self, obj):
        """Return full names of users that can view resource, otherwise return empty array."""
        names = []
        if hasattr(obj, 'raccess'):
            for viewer in obj.raccess.view_users.all():
                name = viewer.first_name + ' ' + viewer.last_name
                names.append(name)
        return names

    def prepare_viewers_count(self, obj):
        """Return count of users who can view resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.view_users.all().count()
        else:
            return 0

    def prepare_editors_logins(self, obj):
        """Return usernames of editors of a resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return [editor.username for editor in obj.raccess.edit_users.all()]
        else:
            return 0

    def prepare_editors_names(self, obj):
        """Return full names of editors of a resource, otherwise return empty array."""
        names = []
        if hasattr(obj, 'raccess'):
            for editor in obj.raccess.edit_users.all():
                name = editor.first_name + ' ' + editor.last_name
                names.append(name)
        return names

    def prepare_editors_count(self, obj):
        """Return count of editors of a resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.edit_users.all().count()
        else:
            return 0

    def prepare_absolute_url(self, obj):
        """Return absolute URL of object."""
        return obj.get_absolute_url()

    def prepare_ontology_id(self, obj):
        if 'ontology_ids' in obj.extra_data:
            ids_str = obj.extra_data['ontology_ids']
            ids_list = ids_str.split(',')
            return ids_list
        else:
            return []
