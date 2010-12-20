from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib import databrowse

from django.contrib import admin
admin.autodiscover()


#from shapeft.custom_admin import editor
#from registration.views import register

urlpatterns = patterns('',
    (r'^_admin_/', include(admin.site.urls)),
#    (r'^editor/(.*)', editor.root),
    (r'^databrowse/(.*)', databrowse.site.root),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DATA}),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),        
    (r'^comments/', include('django.contrib.comments.urls')), 

    (r'^contact/', include('contact.urls')),
    (r'^auth/', include('ft_auth.urls')),
    (r'^', include('shapeft.urls')),

)
