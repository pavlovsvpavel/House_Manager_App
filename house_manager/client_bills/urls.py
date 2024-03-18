from django.urls import path

from house_manager.client_bills.views import ClientBillsDetailsView, CurrentClientBillEditView, \
    ClientOtherBillsDetailsView, CurrentClientOtherBillEditView

urlpatterns = (
    path("<int:pk>/list/", ClientBillsDetailsView.as_view(), name="list_client_bills"),
    path("<int:pk>/details/", CurrentClientBillEditView.as_view(), name="edit_client_bill"),
    path("<int:pk>/other-bills-list/", ClientOtherBillsDetailsView.as_view(), name="list_other_client_bills"),
    path("<int:pk>/details-other-bills/", CurrentClientOtherBillEditView.as_view(), name="edit_client_other_bill"),
)
