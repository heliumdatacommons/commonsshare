__author__ = 'tonycastronova'

from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from hs_model_program.models import MpMetadata
from hs_core.forms import BaseFormHelper

class mp_form_helper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):

        files = kwargs.pop('files')
        file_data = {}
        for f in files.all():
            short_url = f.resource_file.name
            name = short_url.split('/')[-1]
            file_data[name] = short_url

        options = '\n'.join(['<option value=%s>%s</option>'%(value, key) for key, value in file_data.iteritems() ])

        multiselect_elements = ['modelSoftware', 'modelDocumentation', 'modelReleaseNotes']
        multiselect = {}
        for elem in multiselect_elements:
            # build select list and selection table
            multiselect[elem] = HTML(
                            '<div class="div-multi-select" parent_metadata="'+elem+'">'
                                ' <select class="multi-select" id="multi-select" multiple="multiple">'
                                        + options +
                                '</select>'
                                '<div id="div_section_table" style="display:none">'
                                    '<table class="table table-condensed table-hover table-bordered" id="section_table">'
                                    '</table>'
                                '</div>'
                            '</div>')


        # Order of the Fields below determines their layout on the edit page
        # For consistency, make sure this ordering matches models.py->get_xml()
        field_width = 'form-control input-sm'
        css_multichar = field_width + ' multichar'
        layout = Layout(
            Field('modelSoftware', css_class=css_multichar, style="display:none"),
            multiselect['modelSoftware'],
            Field('modelDocumentation', css_class=css_multichar, style="display:none"),
            multiselect['modelDocumentation'],
            Field('modelReleaseNotes', css_class=css_multichar, style="display:none"),
            multiselect['modelReleaseNotes'],
            Field('modelReleaseDate', css_class=field_width),
            Field('modelVersion', css_class=field_width),
            Field('modelWebsite', css_class=field_width),
            Field('modelProgramLanguage', css_class=field_width),
            Field('modelOperatingSystem', css_class=field_width),
            Field('modelCodeRepository', css_class=field_width),
        )
        super(mp_form_helper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='  ',  *args, **kwargs)


class mp_form(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        # pop files from kwargs, else metadata will fail to load in edit mode
        files = kwargs.pop('files')
        super(mp_form, self).__init__(*args, **kwargs)
        self.helper = mp_form_helper(allow_edit, res_short_id, element_id, element_name='MpMetadata', files=files)


        # Set the choice lists as the file names in the content model
        # filenames = ['       '] + [f.resource_file.name.split('/')[-1] for f in files.all()]
        # CHOICES = tuple((f, f) for f in filenames)
        # self.fields['modelReleaseNotes'].choices = CHOICES
        # self.fields['modelDocumentation'].choices = CHOICES
        # self.fields['modelSoftware'].choices = CHOICES

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'has-popover', 'data-content':help_text, 'data-placement':'right', 'data-container':'body'})


    class Meta:
        model = MpMetadata

        fields = [  'modelVersion',
                    'modelProgramLanguage',
                    'modelOperatingSystem',
                    'modelReleaseDate',
                    'modelWebsite',
                    'modelCodeRepository',
                    'modelReleaseNotes',
                    'modelDocumentation',
                    'modelSoftware']
        exclude = ['content_object']


class mp_form_validation(forms.Form):
    modelVersion = forms.CharField(required=False)
    modelProgramLanguage = forms.CharField(required=False)
    modelOperatingSystem = forms.CharField(required=False)
    modelReleaseDate = forms.DateTimeField(required=False)
    modelWebsite = forms.CharField(required=False)
    modelCodeRepository = forms.CharField(required=False)
    modelReleaseNotes = forms.CharField(required=False)
    modelDocumentation = forms.CharField(required=False)
    modelSoftware = forms.CharField(required=False)


