from django.http import HttpResponse
from django.template import loader
from apps.project.models import Project, Term
from django.core.cache import cache


def sitemap_style(request):
    template = loader.get_template('./main-sitemap.xsl')
    return HttpResponse(template.render({}, request), content_type='text/xml')


def sitemap_index(request):
    sm = [
        "https://koinhunt.com/project-sitemap.xml",
        "https://koinhunt.com/category-sitemap.xml",
        "https://koinhunt.com/tag-sitemap.xml",
        "https://koinhunt.com/chain-sitemap.xml"
    ]
    template = loader.get_template('./sitemap_index.xml')
    return HttpResponse(template.render({
        "sitemaps": sm
    }, request), content_type='text/xml')


def sitemap_detail(request, flag):
    template = loader.get_template('./sitemap.xml')
    if flag == "project":
        ds = list(map(
            lambda x: {
                "location": "https://koinhunt.com/project/{}".format(x.id_string),
                "priority": 0.8,
                "updated": x.updated,
                "changefreq": "daily"
            },
            Project.objects.all()
        ))
    else:
        ds = list(map(
            lambda x: {
                "location": "https://koinhunt.com/{}/{}".format(flag, x.id_string),
                "priority": 0.5,
                "updated": x.updated,
                "changefreq": "daily"
            },
            Term.objects.all()
        ))
    return HttpResponse(template.render({
        "dataset": ds
    }, request), content_type='text/xml')

