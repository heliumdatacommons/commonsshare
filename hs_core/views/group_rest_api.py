from rest_framework.views import APIView
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_200_OK
from rest_framework.response import Response

class GroupInfo(APIView):
    def get(self, request):
        """
        Retrieve the requesting user's groups list
        :param request:
        :return: list of groups the requesting user is in
        """
        if not request.user.is_authenticated():
            return Response(data='you are not authenticated', status=HTTP_403_FORBIDDEN)

        gcnt = request.user.uaccess.view_groups.count()

        if gcnt <= 0:
            # the request user is not in any group
            return Response(data='you are not in any group', status=HTTP_200_OK)

        group_list = []
        for g in request.user.uaccess.view_groups:
            group_info = {}
            member_list = []
            for u in g.gaccess.members:
                member_list.append({
                    'id': u.id,
                    'name': u.username
                })
            group_info['id'] = g.id
            group_info['name'] = g.name
            group_info['members'] = member_list
            group_list.append(group_info)

        return Response(data=group_list, status=HTTP_200_OK)
