from django.http import JsonResponse

import requests, os, tempfile

from hs_restclient import HydroShare
from tethys_services.backends.hs_restclient_helper import get_oauth_hs

message_template_wrong_req_method = 'This request can only be made through a "{method}" AJAX call.'
message_template_param_unfilled = 'The required "{param}" parameter was not fulfilled.'


def get_epanet_model_list(request):
    """
    This is an example controller that uses the HydroShare API.
    """
    return_obj = {
        'success': False,
        'message': None,
        'model_list': None
    }

    if request.is_ajax() and request.method == 'GET':
        try:
            hs = get_oauth_hs(request)
        except:
            hs = HydroShare()

        model_list = []

        try:
            for model in hs.resources(type="ModelInstanceResource"):

                science_metadata_json = hs.getScienceMetadata(model['resource_id'])

                if not science_metadata_json['executed_by'] is None:
                    if science_metadata_json['executed_by']['modelProgramName'] == 'EPANET_2.0':
                        subjects = []
                        for subject in science_metadata_json['subjects']:
                            subjects.append(" " + subject['value'])

                        model_list.append({
                            'title': model['resource_title'],
                            'id': model['resource_id'],
                            'type': model['resource_type'],
                            'owner': model['creator'],
                            'subjects': subjects,
                        })

            return_obj['model_list'] = model_list
            return_obj['success'] = True

        except:
            return_obj['message'] = 'The HydroShare server appears to be down.'
    else:
        return_obj['error'] = message_template_wrong_req_method.format(method="GET")

    return JsonResponse(return_obj)


def get_epanet_model(request):
    return_obj = {
        'success': False,
        'message': None,
        'results': "",
        'metadata': ""
    }
    if request.is_ajax() and request.method == 'GET':
        if not request.GET.get('model_id'):
            return_obj['message'] = message_template_param_unfilled.format(param='model_id')
        else:
            model_id = request.GET['model_id']

            try:
                hs = get_oauth_hs(request)
            except:
                hs = HydroShare()

            print(hs.getSystemMetadata(model_id))

            metadata_json = hs.getScienceMetadata(model_id)
            return_obj['metadata'] = metadata_json

            for model_file in hs.getResourceFileList(model_id):
                model = requests.get(model_file["url"])
                return_obj['results'] = model.text
                return_obj['success'] = True

    else:
        return_obj['message'] = message_template_wrong_req_method.format(method="GET")

    return JsonResponse(return_obj)


def upload_epanet_model(request):
    return_obj = {
        'success': False,
        'message': None,
        'results': "",
    }

    if request.is_ajax() and request.method == 'POST':
        try:
            hs = get_oauth_hs(request)
        except:
            hs = HydroShare()

        model_title = request.POST['model_title']
        resource_filename = model_title + ".inp"

        abstract = request.POST['model_description']
        title = model_title
        keywords = (tuple(request.POST['model_keywords'].split(",")))
        rtype = 'ModelInstanceResource'
        extra_metadata = '{"modelProgram": "EPANET_2.0"}'

        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(request.POST['model_file'])
            fpath = path

        metadata = '[{"creator":{"name":"' + hs.getUserInfo()['first_name'] + ' ' + hs.getUserInfo()['last_name'] + '"}}]'
        resource_id = hs.createResource(rtype, title, resource_file=fpath, resource_filename=resource_filename, keywords=keywords, abstract=abstract, metadata=metadata, extra_metadata=extra_metadata)

        hs.setAccessRules(resource_id, public=True)

        return_obj['results'] = resource_id
        return_obj['success'] = True

    else:
        return_obj['message'] = message_template_wrong_req_method.format(method="GET")

    return JsonResponse(return_obj)
