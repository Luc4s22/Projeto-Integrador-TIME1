from django.urls import re_path

from .views import ChatView

urlpatterns = [
    # POST /api/v1/chat {"message": "...", "shipment_id": opcional}
    re_path(r'^chat/?$', ChatView.as_view(), name='chat'),
]
