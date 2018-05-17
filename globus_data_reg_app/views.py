import json
import os
import string
from django.http import HttpResponse, HttpResponseRedirect


def search_ds(coll):
    store = {}
    file = []
    folder = []
    if coll.data_objects:
        for files in coll.data_objects:
            file.append(files.name)
    if coll.subcollections:
        for folders in coll.subcollections:
            folder.append(folders.name)

    store['files'] = file
    store['folder'] = folder
    return store


# Create your views here.
def store(request):
    """
    Get file hierarchy for the requested endpoint directory in globus.
    It is invoked by an AJAX call, so it returns json object that holds content for files and folders
    under the requested directory/collection/subcollection
    """
    return_object = {}
    datastore = str(request.POST['store'])
    coll = irods_sess.collections.get(datastore)
    store = search_ds(coll)

    return_object['files'] = store['files']
    return_object['folder'] = store['folder']
    jsondump = json.dumps(return_object)
    irods_sess.cleanup()
    return HttpResponse(
        jsondump,
        content_type = "application/json"
    )

def register(request):
    if request.method == 'POST':
        file_names = str(request.POST['upload'])
        fnames_list = string.split(file_names, ',')

        response_data = {}
        response_data['file_type_error'] = ''
        response_data['irods_file_names'] = file_names
        # get selected file names without path for informational display on the page
        response_data['irods_sel_file'] = ', '.join(os.path.basename(f.rstrip(os.sep)) for f in fnames_list)
        homepath = fnames_list[0]
        response_data['irods_federated'] = utils.is_federated(homepath)
        response_data['is_file_reference'] = request.POST['file_ref']

        return HttpResponse(
            json.dumps(response_data),
            content_type = "application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "Not POST request"}),
            content_type="application/json"
        )

