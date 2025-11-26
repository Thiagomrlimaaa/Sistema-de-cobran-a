from django.urls import path

from .views import (
    BotControlView,
    ContactImportView,
    DashboardHomeView,
    ClientCreateView,
    ClientDeleteView,
    ClientListView,
    ClientUpdateView,
    TriggerMessageView,
)

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("clients/", ClientListView.as_view(), name="clients"),
    path("clients/novo/", ClientCreateView.as_view(), name="client-create"),
    path("clients/<int:pk>/editar/", ClientUpdateView.as_view(), name="client-update"),
    path("clients/<int:pk>/excluir/", ClientDeleteView.as_view(), name="client-delete"),
    path("clients/importar/", ContactImportView.as_view(), name="client-import"),
    path("clients/enviar/", TriggerMessageView.as_view(), name="client-send-message"),
    path("bot/", BotControlView.as_view(), name="bot-control"),
]


