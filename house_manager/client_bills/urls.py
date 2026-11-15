from django.urls import path

from house_manager.client_bills.views import (
    ClientMonthlyBillsDetailView, CurrentClientMonthlyBillEditView,
    ClientOtherBillsDetailView, CurrentClientOtherBillEditView, DownloadReceiptView,
    CurrentClientMonthlyBillRevertView, CurrentClientOtherBillRevertView
)

# Mounted at: houses/<int:house_pk>/clients/<int:client_pk>/
urlpatterns = (
    path("bills/", ClientMonthlyBillsDetailView.as_view(), name="list_client_bills"),
    path("bills/<int:pk>/edit/", CurrentClientMonthlyBillEditView.as_view(), name="edit_client_bill"),
    path("bills/<int:pk>/revert/", CurrentClientMonthlyBillRevertView.as_view(), name="revert_client_bill"),
    path("bills/<int:pk>/receipt/download/", DownloadReceiptView.as_view(), name="download_receipt"),
    path("other-bills/", ClientOtherBillsDetailView.as_view(), name="list_other_client_bills"),
    path("other-bills/<int:pk>/edit/", CurrentClientOtherBillEditView.as_view(), name="edit_client_other_bill"),
    path("other-bills/<int:pk>/revert/", CurrentClientOtherBillRevertView.as_view(), name="revert_client_other_bill"),
)
