from django.urls import path
from house_manager.client_bills.views import (
    ClientMonthlyBillsDetailView, CurrentClientMonthlyBillEditView,
    ClientOtherBillsDetailView, CurrentClientOtherBillEditView
)

urlpatterns = (
    path("bills/<int:pk>/", ClientMonthlyBillsDetailView.as_view(), name="list_client_bills"),
    path("edit-bill/<int:pk>/", CurrentClientMonthlyBillEditView.as_view(), name="edit_client_bill"),
    path("other-bills/<int:pk>/", ClientOtherBillsDetailView.as_view(), name="list_other_client_bills"),
    path("edit-other-bill/<int:pk>/", CurrentClientOtherBillEditView.as_view(), name="edit_client_other_bill"),
)
