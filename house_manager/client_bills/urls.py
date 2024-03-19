from django.urls import path

from house_manager.client_bills.views import ClientMonthlyBillsDetailView, CurrentClientMonthlyBillEditView, \
    ClientOtherBillsDetailView, CurrentClientOtherBillEditView

urlpatterns = (
    path("<int:pk>/list/", ClientMonthlyBillsDetailView.as_view(), name="list_client_bills"),
    path("<int:pk>/details/", CurrentClientMonthlyBillEditView.as_view(), name="edit_client_bill"),
    path("<int:pk>/other-bills-list/", ClientOtherBillsDetailView.as_view(), name="list_other_client_bills"),
    path("<int:pk>/details-other-bills/", CurrentClientOtherBillEditView.as_view(), name="edit_client_other_bill"),
)
