from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "main"

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.CustomLoginView.as_view(), name='login'),
    path('logout', views.logout_view, name='logout'),
    path('visitor_register', views.visitor_register, name='visitor_register'),
    path('client_register', views.client_register, name='client_register'),
    path('profile/<int:pk>', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/update', views.UserInfoUpdateView.as_view(), name='profile_update'),
    path('admin/users', views.AdminListView.as_view(), name='admin_list_users'),
    path('admin/user/<int:pk>/approve', views.AdminApprove.as_view(), name='admin_approve'),
    path('admin/user/<int:pk>/reject', views.AdminReject.as_view(), name='admin_reject'),
    path('admin/user/<int:pk>/comment', views.AdminCommentUpdateView.as_view(), name='admin_comment'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
