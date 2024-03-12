from django.urls import path

from house_manager.client_bills.views import ClientBillsDetailsView, CurrentClientBillEditView


urlpatterns = (
    path("<int:pk>/list/", ClientBillsDetailsView.as_view(), name="list_client_bills"),
    path("<int:pk>/details/", CurrentClientBillEditView.as_view(), name="edit_client_bill"),
)
