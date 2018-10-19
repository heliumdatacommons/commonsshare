from haystack.forms import FacetedSearchForm
from haystack.query import SQ
from django import forms
from django.conf import settings

from haystack_queryparser import ParseSQ, NoMatchingBracketsFound, UnhandledException
import pysolr


class DiscoveryForm(FacetedSearchForm):
    SORT_ORDER_VALUES = ('title', 'author_normalized', 'created', 'modified')
    SORT_ORDER_CHOICES = (('title', 'Title'),
                          ('author_normalized', 'First Author'),
                          ('created', 'Date Created'),
                          ('modified', 'Last Modified'))

    SORT_DIRECTION_VALUES = ('', '-')
    SORT_DIRECTION_CHOICES = (('', 'Ascending'),
                              ('-', 'Descending'))

    sort_order = forms.CharField(label='Sort By:',
                                 widget=forms.Select(choices=SORT_ORDER_CHOICES),
                                 required=False)
    sort_direction = forms.CharField(label='Sort Direction:',
                                     widget=forms.Select(choices=SORT_DIRECTION_CHOICES),
                                     required=False)

    def search(self):
        self.parse_error = None
        sqs = self.searchqueryset.all().filter(is_replaced_by=False)
        if self.cleaned_data.get('q'):
            # The prior code corrected for an failed match of complete words, as documented
            # in issue #2308. This version instead uses an advanced query syntax in which
            # "word" indicates an exact match and the bare word indicates a stemmed match.
            cdata = self.cleaned_data.get('q')
            try:
                # query in CommonsShare core first
                parser = ParseSQ()
                parsed = parser.parse(cdata)
                sqs = sqs.filter(parsed)

                # then query against ontology-core using pysolr
                ontology_solr = pysolr.Solr(settings.ONTOLOGY_SOLR_URL)
                oresults = ontology_solr.search(q='isa_partof_closure_label:*' + cdata + '*',
                                                rows=settings.MAX_ROWS_IN_ONTOLOGY_CORE)
                if len(oresults) > 0:
                    cs_sqs = sqs
                    ids = [result['id'] for result in oresults]
                    # cannot query with over 1000 ids OR'ed together due to URL length constraint,
                    # so need to break the OR query into multiples
                    rows_in_single_query = 1000
                    if len(ids) < rows_in_single_query:
                        id_chunks = [ids]
                    else:
                        id_chunks = [ids[x:x+rows_in_single_query] for x in
                                     range(0, len(ids), rows_in_single_query)]

                    sub_sqs_list = []
                    for id_chunk in id_chunks:
                        id_chunk[0] = 'ontology_id:{}'.format(id_chunk[0])
                        squery = ' OR ontology_id:'.join(id_chunk)
                        parsed = parser.parse(squery)
                        sqs = self.searchqueryset.all().filter(is_replaced_by=False)
                        sub_sqs_list.append(sqs.filter(parsed))
                    # merge all sub-queries
                    if len(sub_sqs_list) > 0:
                        sqs = cs_sqs | sub_sqs_list[0]
                    for sub_sqs in sub_sqs_list[1:]:
                        sqs = sqs | sub_sqs
            except NoMatchingBracketsFound as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "{} No matches. Please try again.".format(e.value)
                return sqs
            except UnhandledException as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "{} No matches. Please try again.".format(e.value)
                return sqs

        authors_sq = None
        subjects_sq = None
        resource_type_sq = None
        public_sq = None
        owners_names_sq = None
        discoverable_sq = None
        published_sq = None

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:

        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)
            value = sqs.query.clean(value)

            if value:
                if "creators" in field:
                    if authors_sq is None:
                        authors_sq = SQ(creators=value)
                    else:
                        authors_sq.add(SQ(creators=value), SQ.OR)

                elif "subjects" in field:
                    if subjects_sq is None:
                        subjects_sq = SQ(subjects=value)
                    else:
                        subjects_sq.add(SQ(subjects=value), SQ.OR)

                elif "resource_type" in field:
                    if resource_type_sq is None:
                        resource_type_sq = SQ(resource_type=value)
                    else:
                        resource_type_sq.add(SQ(resource_type=value), SQ.OR)

                elif "public" in field:
                    if public_sq is None:
                        public_sq = SQ(public=value)
                    else:
                        public_sq.add(SQ(public=value), SQ.OR)

                elif "owners_names" in field:
                    if owners_names_sq is None:
                        owners_names_sq = SQ(owners_names=value)
                    else:
                        owners_names_sq.add(SQ(owners_names=value), SQ.OR)

                elif "discoverable" in field:
                    if discoverable_sq is None:
                        discoverable_sq = SQ(discoverable=value)
                    else:
                        discoverable_sq.add(SQ(discoverable=value), SQ.OR)

                elif "published" in field:
                    if published_sq is None:
                        published_sq = SQ(published=value)
                    else:
                        published_sq.add(SQ(published=value), SQ.OR)

                else:
                    continue

        if authors_sq is not None:
            sqs = sqs.filter(authors_sq)
        if subjects_sq is not None:
            sqs = sqs.filter(subjects_sq)
        if resource_type_sq is not None:
            sqs = sqs.filter(resource_type_sq)
        if public_sq is not None:
            sqs = sqs.filter(public_sq)
        if owners_names_sq is not None:
            sqs = sqs.filter(owners_names_sq)
        if discoverable_sq is not None:
            sqs = sqs.filter(discoverable_sq)
        if published_sq is not None:
            sqs = sqs.filter(published_sq)

        return sqs
