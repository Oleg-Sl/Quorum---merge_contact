from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('merge_contacts/admin/', admin.site.urls),
    path('merge_contacts/api/v1/', include('api_v1.urls', namespace='api_v1')),
]

