from django.urls import path

from mysite.ibfm import views

urlpatterns = [
    path('ibfm/', views.bid_files_list, name='ibidFilesHome'),
    path('ibfm/add', views.bidfiles_add, name='ibidFilesAdd'),
    path('ibfm/edit/<int:bidfiles_id>', views.bidfiles_edit, name='ibidFilesEdit'),
    path('ibfm/archive/<int:bidfiles_id>/', views.bidfiles_archive, name='ibidFilesArchive'),
    path('ibfm/delete/<int:bidfiles_id>/', views.bidfiles_delete, name='ibidFilesDelete'),
    path('ibfm/pdf_analyzer/project_address/run/<int:bidfile_id>/', views.pdf_analyzer_project_address_run,
         name='ibidFilesPDFAnalyzerProjectAddressRun'),
    path('ibfm/pdf_analyzer/project_address/progress/<int:run_id>/', views.pdf_analyzer_project_address_progress,
         name='ibidFilesPDFAnalyzerProjectAddressProgress'),
    path('ibfm/pdf_analyzer/project_address/progress_json/<int:run_id>/',
         views.pdf_analyzer_project_address_progress_json, name='ibidFilesPDFAnalyzerProjectAddressProgressJson'),
    path('ibfm/pdf_analyzer/project_address/progress_json_all/<int:run_id>/',
         views.pdf_analyzer_project_address_progress_json_all,
         name='ibidFilesPDFAnalyzerProjectAddressProgressJsonAll'),
    path('ibfm/pdf_analyzer/project_address/debug/<int:run_id>/', views.pdf_analyzer_project_address_debug,
         name='ibidFilesPDFAnalyzerProjectAddressDebug'),
]
