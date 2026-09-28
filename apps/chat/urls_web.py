from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),
    path("api/conversations/", views.conversations, name="conversations"),
    path("api/conversations/<uuid:pk>/messages/", views.messages, name="messages"),
    path("api/conversations/<uuid:pk>/send/", views.send, name="send"),
    path("api/direct/<int:user_id>/", views.start_direct, name="direct"),
    path("api/groups/", views.create_group, name="groups"),
    path("api/unread/", views.unread, name="unread"),
    path("media/<int:pk>/", views.media, name="media"),
]
