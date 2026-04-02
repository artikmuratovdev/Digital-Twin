from django.urls import path

from .views import (
    add_history_view,
    ai_chat_view,
    ai_summary_view,
    home_view,
    patient_create_view,
    patient_detail_view,
    predict_view,
    simulate_view,
)


urlpatterns = [
    path("", home_view, name="home"),
    path("patients/new/", patient_create_view, name="patient_create"),
    path("patients/<int:patient_id>/", patient_detail_view, name="patient_detail"),
    path("predict/", predict_view, name="predict"),
    path("simulate/<int:patient_id>/", simulate_view, name="simulate"),
    path("history/<int:patient_id>/add/", add_history_view, name="add_history"),
    path("ai/summary/<int:patient_id>/", ai_summary_view, name="ai_summary"),
    path("ai/chat/<int:patient_id>/", ai_chat_view, name="ai_chat"),
]
