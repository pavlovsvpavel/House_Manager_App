from django.urls import path

from house_manager.client_bills.views import (
    ClientMonthlyBillsDetailView, CurrentClientMonthlyBillEditView,
    ClientOtherBillsDetailView, CurrentClientOtherBillEditView
)

urlpatterns = (
    path("<int:pk>/bills/", ClientMonthlyBillsDetailView.as_view(), name="list_client_bills"),
    path("<int:pk>/edit-bill/", CurrentClientMonthlyBillEditView.as_view(), name="edit_client_bill"),
    path("<int:pk>/other-bills/", ClientOtherBillsDetailView.as_view(), name="list_other_client_bills"),
    path("<int:pk>/edit-other-bill/", CurrentClientOtherBillEditView.as_view(), name="edit_client_other_bill"),
)
