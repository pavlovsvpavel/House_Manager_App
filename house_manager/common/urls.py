from django.urls import path
from house_manager.common.views import IndexView, DashboardView, about_view, ReportMonthlyBillView, ReportOtherBillView

urlpatterns = (
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("about/", about_view, name="about"),
    path('reports-bills/<int:pk>/', ReportMonthlyBillView.as_view(), name='reports_bills'),
    path('reports-other-bills/<int:pk>/', ReportOtherBillView.as_view(), name='reports_other_bills'),
)

