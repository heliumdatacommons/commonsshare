from django.views.generic import TemplateView

from hs_tools_resource.models import ToolResource
from hs_core.views.utils import get_url_with_token


class AppsView(TemplateView):
    template_name = "pages/apps.html"

    def get_context_data(self, **kwargs):
        context = super(AppsView, self).get_context_data(**kwargs)
        approved_apps = ToolResource.get_approved_apps()
        req = self.request
        web_apps = []
        for app in approved_apps:
            url = app.metadata.app_home_page_url.value
            web_apps.append({'url': get_url_with_token(req, url),
                             'resource': app})
        context['webapp_resources'] = web_apps
        return context
