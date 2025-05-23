"""
URL configuration for Lotteria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import home
    2. Add a URL to urlpatterns:  path('', home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from mxh import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('user_home/', views.user_home, name='user_home'),
    path('chat/', views.chat_view, name='chat'),
    path('group_chats/', views.group_chat_list, name='group_chat_list'),
    path('create_post/', views.create_post, name='create_post'),
    path('user_home/', views.post_detail, name='post_detail'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('search/', views.search_employees, name='search_employees'),
    path('chat/<int:chat_id>/', views.chat_room, name='chat_room'),
    path('start_chat/<int:user_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:chat_id>/send/', views.add_message, name='add_message'),
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:group_id>/edit/', views.edit_group_name, name='edit_group_name'),
    path('group/<int:group_id>/add-members/', views.add_members_to_group, name='add_members_to_group'),
    path('group/delete/<int:group_id>/', views.delete_group, name='delete_group'),
    path('group/<int:group_id>/', views.group_chat_room, name='group_chat_room'),
    path('group/<int:group_id>/add_message/', views.add_group_message, name='add_group_message'),
    path('search_add/', views.search_employees_add, name='search_employees_add'),

    path('admin_home/chat-management/', views.admin_chat_management, name='admin_chat_management'),
    path('admin_home/post-management/', views.admin_post_management, name='admin_post_management'),
    path('admin_home/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin_home/notifications/create/', views.admin_notification_create, name='admin_notification_create'),
    path('admin_home/notifications/edit/<int:notification_id>/', views.admin_notification_edit, name='admin_notification_edit'),
    path('admin_home/notifications/delete/<int:notification_id>/', views.admin_notification_delete, name='admin_notification_delete'),
    path('user_home/notifications/', views.notification_view, name='notification_view'),
    path('user_home/notifications/company/', views.notification_company, name='notification_company'),
    path('user_home/notifications/company/<int:pk>/', views.notification_company_detail, name='company_notification_detail'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('task/', views.task_list_view, name='task_view'),
    path('task/create/', views.create_task_view, name='task_create'),
    path('tasks/change-status/<int:task_id>/', views.change_task_status, name='change_task_status'),
    path('task/create_todo', views.create_todo, name='create_todo'),
    path('task/todo_list', views.todo_list, name='todo_list'),
    path('toggle/<int:task_id>/', views.toggle_status, name='toggle_status'),
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),

    path('task/proposal/create/', views.create_proposal, name='create_proposal'),
    path('task/proposal/my/', views.my_proposals, name='proposal_list'),
    path('task/proposal/incoming/', views.incoming_proposals, name='incoming_proposals'),
    path('task/proposal/<int:proposal_id>/review/', views.review_proposal, name='review_proposal'),
    path('task/proposal/<int:proposal_id>/create-task/', views.create_task_from_proposal, name='create_task_from_proposal'),


    path('edit_post/<int:post_id>', views.edit_post, name='edit_post'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/comment-profile/', views.add_comment_profile, name='add_comment_profile'),

    path('send-friend-request/', views.send_friend_request, name='send_friend_request'),
    path('cancel-friend-request/', views.cancel_friend_request, name='cancel_friend_request'),
    path('respond-friend-request/', views.respond_friend_request, name='respond_friend_request'),
    path('unfriend/', views.unfriend, name='unfriend'),
    path('get-friend-status/<int:user_id>/', views.get_friend_status, name='get_friend_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
