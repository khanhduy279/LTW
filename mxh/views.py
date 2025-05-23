import os
import uuid
import json
import logging

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Exists, OuterRef, Subquery, Max, F
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import PostForm, TaskAssignmentForm, NotificationForm, TaskProposalForm, TaskProposalReviewForm
from .context_processors import get_unread_count
from .models import (
    Post, Comment, PrivateChat, PrivateMessage, Friend,
    GroupChat, GroupMember, Message, Notification, UserNotification,
    TaskAssignment, Task, Department, TodoList, Like, TaskProposal
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import GroupChat, GroupMember
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import GroupChat, GroupMember


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_home')
            else:
                return redirect('user_home')
    return render(request, 'mxh/login/login.html')


@login_required
def admin_home(request):
    return render(request, 'mxh/chat/chat_admin.html')


from django.db.models import Exists, OuterRef, Q


@login_required
def user_home(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('user_home')
    else:
        form = PostForm()

    comments = Comment.objects.all()

    likes = Like.objects.filter(user=request.user, post=OuterRef('pk'))
    posts = Post.objects.all().annotate(user_liked=Exists(likes)).order_by('-created_at')

    chat = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).first()

    context = {
        'form': form,
        'posts': posts,
        'comments': comments,
        'default_chat_id': chat.id if chat else None,
    }
    return render(request, 'mxh/home/home.html', context)


# Tạo bài viết
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('user_home')
    else:
        form = PostForm()
    return render(request, 'mxh/home/create_post.html', {'form': form})


# Bình luận
@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        post = get_object_or_404(Post, id=post_id)
        Comment.objects.create(post=post, user=request.user, content=content)
        if post.user != request.user:
            notif = Notification.objects.create(
                sender=request.user,
                title='Bình luận mới',
                content=f'{request.user.username} đã bình luận bài viết của bạn: "{content}"',
                type='personal'
            )
            UserNotification.objects.create(notification=notif, user=post.user)
    return redirect('user_home')


# Danh sách bình luận
@login_required
def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'comments': comments,
    }
    return render(request, 'mxh/home/home.html', context)


# Tìm kiếm tên và bộ phận
User = get_user_model()


@login_required
def search_employees(request):
    query = request.GET.get('q', '')
    department_id = request.GET.get('department', '')

    users = User.objects.all()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    if department_id:
        users = users.filter(department_id=department_id)

    # Nếu là AJAX request, trả về JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar_url': user.avatar_url.url if user.avatar_url else None
            })
        return JsonResponse({'users': user_list})

    # Nếu không phải AJAX, trả về template như cũ
    form = PostForm()
    likes = Like.objects.filter(user=request.user, post=OuterRef('pk'))
    posts = Post.objects.all().annotate(user_liked=Exists(likes)).order_by('-created_at')
    comments = Comment.objects.all()
    departments = Department.objects.all()
    chat = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).first()

    context = {
        'form': form,
        'posts': posts,
        'comments': comments,
        'users': users,
        'query': query,
        'department_id': department_id,
        'departments': departments,
        'default_chat_id': chat.id if chat else None,
    }
    return render(request, 'mxh/home/home.html', context)


# Đếm lượt thích
@login_required
def toggle_like(request):
    if request.method == "POST":
        post_id = request.POST.get('post_id')
        if not post_id:
            return HttpResponseBadRequest("Missing post_id")

        post = get_object_or_404(Post, id=post_id)
        user = request.user
        liked_obj, created = Like.objects.get_or_create(post=post, user=user)
        if not created:
            liked_obj.delete()
            liked_status = False
        else:
            liked_status = True

        if post.user != request.user:
            notif = Notification.objects.create(
                sender=request.user,
                title='Thích bài viết',
                content=f'{request.user.username} đã thích bài viết của bạn.',
                type='personal'
            )
            UserNotification.objects.create(notification=notif, user=post.user)

        like_count = Like.objects.filter(post=post).count()
        return JsonResponse({'liked': liked_status, 'like_count': like_count})

    return HttpResponseBadRequest("Invalid request method")


@login_required
def start_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    chat = PrivateChat.objects.filter(
        Q(user1=request.user, user2=target_user) | Q(user1=target_user, user2=request.user)
    ).first()

    if not chat:
        chat = PrivateChat.objects.create(user1=request.user, user2=target_user)

    return redirect('chat_room', chat_id=chat.id)


# Thêm tin nhắn cá nhân
@login_required
def add_message(request, chat_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        chat = get_object_or_404(PrivateChat, id=chat_id)
        PrivateMessage.objects.create(chat=chat, sender=request.user, content=content)
    return redirect('chat_room', chat_id=chat_id)


# Nhắn tin cá nhân
@login_required
def chat_room(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)
    messages = chat.privatemessage_set.all().order_by('sent_at')
    other_user = chat.get_receiver(request.user)

    chats = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    chat_list = [(c, c.user2 if c.user1 == request.user else c.user1) for c in chats]

    context = {
        'chat': chat,
        'messages': messages,
        'other_user': other_user,
        'chat_list': chat_list,
    }
    return render(request, 'mxh/chat/chat.html', context)


# Hiển thị danh sách tin nhắn
@login_required
def chat_view(request):
    chats = PrivateChat.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    chat_list = []
    for c in chats:
        other = c.user2 if c.user1 == request.user else c.user1
        chat_list.append((c, other))

    context = {
        'chat_list': chat_list,
    }
    return render(request, 'mxh/chat/chat_list.html', context)


# Tạo nhóm chat
@login_required
def create_group(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        member_ids = request.POST.getlist('members')

        group = GroupChat.objects.create(group_name=group_name, created_by=request.user)

        GroupMember.objects.create(group=group, user=request.user, role='admin')

        for member_id in member_ids:
            user = User.objects.get(id=member_id)
            GroupMember.objects.create(group=group, user=user, role='member')

        return redirect('group_chat_list')

    users = User.objects.exclude(id=request.user.id)
    return render(request, 'mxh/chat/create_chat.html', {'users': users})


# Sửa nhóm
from django.shortcuts import get_object_or_404


@login_required
def edit_group_name(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)

    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        member_ids = request.POST.getlist('members')

        group.group_name = group_name
        group.save()
        GroupMember.objects.filter(group=group).exclude(user=request.user).delete()

        for member_id in member_ids:
            if int(member_id) != request.user.id:  # tránh thêm lại admin
                user = User.objects.get(id=member_id)
                GroupMember.objects.create(group=group, user=user, role='member')

        return redirect('group_chat_list')

    users = User.objects.exclude(id=request.user.id)
    current_members = GroupMember.objects.filter(group=group).values_list('user_id', flat=True)

    context = {
        'group': group,
        'users': users,
        'current_members': current_members,
    }
    return render(request, 'mxh/chat/edit_chat.html', context)


# Thêm mới thành viên
@login_required
def add_members_to_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)

    # Exclude admin and existing members
    existing_member_ids = GroupMember.objects.filter(group=group).values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=existing_member_ids)

    if request.method == 'POST':
        selected_user_id = request.POST.get('selected_user')
        if selected_user_id:
            user = User.objects.get(id=selected_user_id)
            GroupMember.objects.create(group=group, user=user, role='member')
            return redirect('group_chat_list')  # hoặc redirect về trang chi tiết nhóm nếu có

    context = {
        'group': group,
        'users': users,
    }
    return render(request, 'mxh/chat/add_member.html', context)


# Xóa nhóm
@login_required
def delete_group(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if request.method == 'POST':
        group.delete()
        return redirect('group_chat_list')
    return render(request, 'mxh/chat/confirm_delete_group.html', {'group': group})


# Tìm kiếm tên thành viên
@login_required
def search_employees_add(request):
    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department', '')

    # Lọc user theo tên hoặc phòng ban nếu có
    users = User.objects.all()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    if department_id:
        users = users.filter(department_id=department_id)

    context = {
        'users': users,
        'query': query,
        'department_id': department_id,
    }
    return render(request, 'mxh/chat/add_member.html', context)


# Nhắn tin trong group
@login_required
def group_chat_room(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    if not GroupMember.objects.filter(group=group, user=request.user).exists():
        return redirect('access_denied')  # hoặc render thông báo tùy bạn

    messages = Message.objects.filter(group=group).order_by('sent_at')
    members = GroupMember.objects.filter(group=group).select_related('user')

    context = {
        'group': group,
        'messages': messages,
        'members': members,
        'username': request.user.username,
    }
    return render(request, 'mxh/chat/group_chat_room.html', context)


# Thêm nhóm mới
@login_required
def add_group_message(request, group_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        group = get_object_or_404(GroupChat, id=group_id)
        Message.objects.create(group=group, sender=request.user, content=content)
    return redirect('group_chat_room', group_id=group_id)


# Hiển thị danh sách nhóm chat
@login_required
def group_chat_list(request):
    user_groups = GroupMember.objects.filter(user=request.user).select_related('group')
    group_chat_list = []
    for group_member in user_groups:
        group = group_member.group
        group_chat_list.append(group)

    context = {
        'group_chat_list': group_chat_list,
    }
    return render(request, 'mxh/chat/group_chat_list.html', context)


# Thông báo phía admin
def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    notifications = Notification.objects.filter(type='company').order_by('-created_at')
    return render(request, 'mxh/admin/notification_list.html', {
        'notifications': notifications,
        'unread_notifications': get_unread_count(request.user)
    })


# Tạo thông báo admin
@login_required
@user_passes_test(is_admin)
def admin_notification_create(request):
    departments = Department.objects.all()

    if request.method == 'POST':
        form = NotificationForm(request.POST, request.FILES)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.sender = request.user
            notification.type = 'company'
            recipient_type = form.cleaned_data['recipient_type']
            notification.is_global = (recipient_type == 'all')
            notification.code = f"TB-{str(uuid.uuid4())[:6].upper()}"

            if request.FILES.get('image'):
                notification.image = request.FILES.get('image')

            notification.save()

            departments_selected = form.cleaned_data['departments']
            if not notification.is_global:
                notification.departments.set(departments_selected)

            users = User.objects.all() if notification.is_global else User.objects.filter(
                department__in=departments_selected)

            UserNotification.objects.bulk_create([
                UserNotification(notification=notification, user=user, is_read=False)
                for user in users
            ])

            messages.success(request, 'Tạo thông báo thành công!')
            return redirect('admin_notifications')
    else:
        form = NotificationForm(initial={'recipient_type': 'all'})

    return render(request, 'mxh/admin/create_edit_notification.html', {
        'form': form,
        'departments': departments,
        'is_edit': False,
    })


# Sửa thông báo admin
@login_required
@user_passes_test(is_admin)
def admin_notification_edit(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    departments = Department.objects.all()

    if request.method == 'POST':
        form = NotificationForm(request.POST, request.FILES, instance=notification)

        if form.is_valid():
            notification = form.save(commit=False)
            recipient_type = form.cleaned_data['recipient_type']
            notification.is_global = (recipient_type == 'all')

            # Xử lý ảnh
            if 'remove_image' in request.POST and notification.image:
                notification.image.delete(save=False)
                notification.image = None
            elif request.FILES.get('image'):
                if notification.image:
                    notification.image.delete(save=False)
                notification.image = request.FILES.get('image')

            notification.save()

            departments_selected = form.cleaned_data['departments']
            if not notification.is_global:
                notification.departments.set(departments_selected)
            else:
                notification.departments.clear()

            # Xóa các user notification cũ
            UserNotification.objects.filter(notification=notification).delete()

            users = User.objects.all() if notification.is_global else User.objects.filter(
                department__in=departments_selected)

            UserNotification.objects.bulk_create([
                UserNotification(notification=notification, user=user, is_read=False)
                for user in users
            ])

            messages.success(request, 'Cập nhật thông báo thành công!')
            return redirect('admin_notifications')
    else:
        initial = {
            'recipient_type': 'all' if notification.is_global else 'department'
        }
        form = NotificationForm(instance=notification, initial=initial)

    selected_departments = notification.departments.values_list('id', flat=True)
    return render(request, 'mxh/admin/create_edit_notification.html', {
        'form': form,
        'departments': departments,
        'is_edit': True,
        'notification': notification,
        'selected_departments': selected_departments,
    })


# Xóa thông báo admin
@login_required
@user_passes_test(is_admin)
def admin_notification_delete(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.method == 'POST':
        if notification.image:
            notification.image.delete(save=False)
        UserNotification.objects.filter(notification=notification).delete()
        notification.delete()
        messages.success(request, 'Xóa thông báo thành công!')
    return redirect('admin_notifications')


@login_required
def notification_view(request):
    # Lấy thông báo cá nhân
    personal_notifications = Notification.objects.filter(
        usernotification__user=request.user,
        type='personal'
    ).order_by('-created_at')

    user_notifications = UserNotification.objects.filter(
        user=request.user,
        notification__in=personal_notifications
    )
    read_notifications = set(user_notifications.filter(is_read=True).values_list('notification_id', flat=True))

    for notification in personal_notifications:
        notification.is_read = notification.id in read_notifications

    personal_unread_count = get_unread_count(request.user, 'personal')

    user_departments = request.user.department
    company_notifications = Notification.objects.filter(
        type='company'
    ).filter(
        Q(is_global=True) |
        Q(departments=user_departments)
    ).distinct().order_by('-created_at')

    company_unread_count = get_unread_count(request.user, 'company')

    return render(request, 'mxh/notification/notification_personal.html', {
        'personal_notifications': personal_notifications,
        'personal_unread_count': personal_unread_count,
        'company_notifications': company_notifications,
        'company_unread_count': company_unread_count,

    })


@login_required
def notification_company(request):
    user_departments = request.user.department

    company_notifications = Notification.objects.filter(
        type='company'
    ).filter(
        Q(is_global=True) |
        Q(departments=user_departments)
    ).distinct().order_by('-created_at')

    user_notifications = UserNotification.objects.filter(
        user=request.user,
        notification__in=company_notifications
    )
    read_notifications = set(user_notifications.filter(is_read=True).values_list('notification_id', flat=True))

    for notification in company_notifications:
        notification.is_read = notification.id in read_notifications

    company_unread_count = get_unread_count(request.user, 'company')

    personal_notifications = Notification.objects.filter(
        usernotification__user=request.user,
        type='personal'
    ).order_by('-created_at')

    UserNotification.objects.filter(
        user=request.user,
        notification__in=personal_notifications,
        is_read=False
    ).update(is_read=True)

    personal_unread_count = get_unread_count(request.user, 'personal')

    return render(request, 'mxh/notification/notification_company.html', {
        'company_notifications': company_notifications,
        'company_unread_count': company_unread_count,
        'personal_unread_count': personal_unread_count,
        'personal_notifications': personal_notifications
    })


@login_required
def notification_company_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk, type='company')

    user_notification, created = UserNotification.objects.get_or_create(
        user=request.user,
        notification=notification
    )
    if not user_notification.is_read:
        user_notification.is_read = True
        user_notification.save()

    personal_notifications = Notification.objects.filter(
        usernotification__user=request.user,
        type='personal'
    ).order_by('-created_at')

    company_notifications = Notification.objects.filter(
        type='company'
    ).filter(
        Q(is_global=True) |
        Q(departments=request.user.department)
    ).distinct().order_by('-created_at')

    personal_unread_count = get_unread_count(request.user, 'personal')
    company_unread_count = get_unread_count(request.user, 'company')

    return render(request, 'mxh/notification/company_notification_detail.html', {
        'notification': notification,
        'personal_notifications': personal_notifications,
        'company_notifications': company_notifications,
        'personal_unread_count': personal_unread_count,
        'company_unread_count': company_unread_count,
        'selected_tab': 'company'
    })


@login_required
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    base_posts = Post.objects.filter(user=profile_user).order_by('-created_at')

    likes = Like.objects.filter(user=request.user, post=OuterRef('pk'))
    user_posts = base_posts.annotate(user_liked=Exists(likes)).prefetch_related('comments', 'like_set')

    post_count = base_posts.count()

    return render(request, 'mxh/profile/profile.html', {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'post_count': post_count,
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        new_image = request.FILES.get('new_image')
        remove_image = request.POST.get('remove_image')

        post.title = title

        if remove_image == 'true':
            post.avatar_url.delete(save=False)
            post.avatar_url = None
        elif new_image:
            post.avatar_url = new_image

        post.save()
        return redirect('user_profile', username=request.user.username)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()

    return redirect('user_profile', username=request.user.username)


@login_required
def add_comment_profile(request, post_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        post = get_object_or_404(Post, id=post_id)
        Comment.objects.create(post=post, user=request.user, content=content)

        # Tạo thông báo nếu người bình luận khác chủ bài viết
        if post.user != request.user:
            notif = Notification.objects.create(
                sender=request.user,
                title='Bình luận mới',
                content=f'{request.user.username} đã bình luận bài viết của bạn: "{content}"',
                type='personal'
            )
            UserNotification.objects.create(notification=notif, user=post.user)
        # Chuyển hướng về trang profile của người sở hữu bài viết
        return redirect('user_profile', username=post.user.username)

    return redirect('user_home')  # fallback nếu không phải POST


# Công việc
from .forms import TaskAssignmentForm
from .models import Task, TaskAssignment


@login_required
def create_task_view(request):
    if request.method == 'POST':
        form = TaskAssignmentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.status = 'pending'  # Gán mặc định
            task.save()

            for user in form.cleaned_data['users']:
                TaskAssignment.objects.create(task=task, user=user)

            return redirect('task_view')
    else:
        form = TaskAssignmentForm(user=request.user)

    return render(request, 'mxh/task/taskform.html', {'form': form})


@login_required
def task_list_view(request):
    tasks_assigned_by_me = Task.objects.filter(assigned_by=request.user)
    assignments = TaskAssignment.objects.filter(user=request.user).select_related('task')

    pending_tasks = set(a.task for a in assignments if a.task.status == 'pending') | \
                    set(task for task in tasks_assigned_by_me if task.status == 'pending')

    completed_tasks = set(a.task for a in assignments if a.task.status == 'completed') | \
                      set(task for task in tasks_assigned_by_me if task.status == 'completed')
    for task in pending_tasks:
        assigned_users = [assignment.user for assignment in TaskAssignment.objects.filter(task=task)]
        task.assigned_to = assigned_users
        task.can_delete = (request.user.role == 'manager')

    for task in completed_tasks:
        assigned_users = [assignment.user for assignment in TaskAssignment.objects.filter(task=task)]
        task.assigned_to = assigned_users
        task.can_delete = (request.user.role == 'manager')
    context = {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'assignments': assignments,  # Truyền assignments vào context
    }
    return render(request, 'mxh/task/task.html', context)


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user = request.user

    assigned_users = TaskAssignment.objects.filter(task=task).values_list('user', flat=True)
    if task.assigned_by == user or (user.id in assigned_users and task.status == 'completed'):
        task.delete()
        return redirect('task_view')

    return HttpResponseForbidden("Bạn không có quyền xoá task này.")


@login_required
def task_list(request):
    pending_tasks = Task.objects.filter(status='pending')
    completed_tasks = Task.objects.filter(status='completed')
    return render(request, 'task_list.html', {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks
    })


@login_required
def change_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.assigned_by == request.user or \
            task.taskassignment_set.filter(user=request.user).exists():
        if request.method == 'POST':
            if 'status' in request.POST:
                task.status = 'completed'
            else:
                task.status = 'pending'
            task.save()

    return redirect('task_view')


@login_required
def create_proposal(request):
    if request.method == 'POST':
        form = TaskProposalForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.proposer = request.user
            proposal.save()
            messages.success(request, "Đã gửi đề xuất công việc.")
            return redirect('proposal_list')
    else:
        form = TaskProposalForm(user=request.user)
    return render(request, 'mxh/task/proposal/create_proposal.html', {'form': form})


@login_required
def my_proposals(request):
    proposals = TaskProposal.objects.filter(proposer=request.user).order_by('-created_at')
    return render(request, 'mxh/task/proposal/my_proposals.html', {'proposals': proposals})


@login_required
def incoming_proposals(request):
    user = request.user
    # Chỉ nhận đề xuất nếu là người quản lý phòng ban nào đó
    if user.role == 'manager':
        proposals = TaskProposal.objects.filter(to_department__manager=user)
    else:
        proposals = TaskProposal.objects.none()
    return render(request, 'mxh/task/proposal/incoming.html', {'proposals': proposals})


@login_required
def review_proposal(request, proposal_id):
    proposal = get_object_or_404(TaskProposal, pk=proposal_id)
    if request.user.role != 'manager' or request.user.department != proposal.to_department:
        return HttpResponseForbidden("Không có quyền phê duyệt.")

    if request.method == 'POST':
        form = TaskProposalReviewForm(request.POST, instance=proposal)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.reviewed_by = request.user
            proposal.reviewed_at = timezone.now()
            proposal.save()
            messages.success(request, "Đã xử lý đề xuất.")
            return redirect('incoming_proposals')
    else:
        form = TaskProposalReviewForm(instance=proposal)

    return render(request, 'mxh/task/proposal/review.html', {'form': form, 'proposal': proposal})


@login_required
def create_task_from_proposal(request, proposal_id):
    proposal = get_object_or_404(TaskProposal, pk=proposal_id, status='approved')

    if request.method == 'POST':
        form = TaskAssignmentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user

            if not task.image:
                task.image = proposal.image
            if not task.document:
                task.document = proposal.document

            task.save()

            for user in form.cleaned_data.get('users', []):
                TaskAssignment.objects.create(task=task, user=user)

            messages.success(request, "Đã tạo công việc từ đề xuất.")
            return redirect('task_view')
    else:
        form = TaskAssignmentForm(user=request.user, initial={
            'task_name': proposal.title,
            'description': proposal.description,
            'deadline': timezone.now().date(),
        })

    return render(request, 'mxh/task/proposal/create_task_from_proposal.html', {
        'form': form,
        'proposal': proposal
    })


# to do list
@login_required
def create_todo(request):
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        if task_name:
            TodoList.objects.create(
                user=request.user,
                task_name=task_name,
                status='pending'
            )
        return redirect('todo_list')

    return render(request, 'mxh/task/todo_list.html')


@login_required
def todo_list(request):
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        if task_name:
            TodoList.objects.create(user=request.user, task_name=task_name)
        return redirect('todo_list')

    tasks = TodoList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'mxh/task/todo_list.html', {'tasks': tasks})


@login_required
def toggle_status(request, task_id):
    task = get_object_or_404(TodoList, id=task_id, user=request.user)
    task.status = 'completed' if task.status == 'pending' else 'pending'
    task.save()
    return redirect('todo_list')


@login_required
def delete_todo_task(request, task_id):
    task = get_object_or_404(TodoList, id=task_id, user=request.user)
    task.delete()
    return redirect('todo_list')


# Chức năng kết bạn
@login_required
def send_friend_request(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin người dùng'})

        try:
            receiver = User.objects.get(id=user_id)

            # Kiểm tra xem đã có lời mời kết bạn nào chưa
            existing_request = Friend.objects.filter(
                (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
            ).first()

            if existing_request:
                return JsonResponse({'status': 'error', 'message': 'Đã có lời mời kết bạn'})

            # Tạo lời mời kết bạn mới
            friend_request = Friend.objects.create(
                sender=request.user,
                receiver=receiver,
                status='pending'
            )

            # Tạo thông báo cho người nhận
            notification = Notification.objects.create(
                sender=request.user,
                title='Lời mời kết bạn',
                content=f'{request.user.username} đã gửi cho bạn lời mời kết bạn',
                type='personal'
            )

            UserNotification.objects.create(
                notification=notification,
                user=receiver,
                is_read=False
            )

            return JsonResponse({'status': 'success'})

        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người dùng'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Phương thức không được hỗ trợ'})


@login_required
def cancel_friend_request(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin người dùng'})

        try:
            receiver = User.objects.get(id=user_id)

            # Tìm và xóa lời mời kết bạn
            friend_request = Friend.objects.filter(
                sender=request.user,
                receiver=receiver,
                status='pending'
            ).first()

            if friend_request:
                # Xóa thông báo liên quan
                notifications = Notification.objects.filter(
                    sender=request.user,
                    title='Lời mời kết bạn',
                    usernotification__user=receiver
                )

                for notification in notifications:
                    UserNotification.objects.filter(
                        notification=notification,
                        user=receiver
                    ).delete()
                    notification.delete()

                friend_request.delete()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Không tìm thấy lời mời kết bạn'})

        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người dùng'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Phương thức không được hỗ trợ'})


@login_required
def respond_friend_request(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        if not request_id or not action:
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin'})

        try:
            friend_request = Friend.objects.get(id=request_id, receiver=request.user, status='pending')

            if action == 'accept':
                friend_request.status = 'accepted'
                friend_request.save()

                # Tạo thông báo cho người gửi
                notification = Notification.objects.create(
                    sender=request.user,
                    title='Lời mời kết bạn được chấp nhận',
                    content=f'{request.user.username} đã chấp nhận lời mời kết bạn của bạn',
                    type='personal'
                )

                UserNotification.objects.create(
                    notification=notification,
                    user=friend_request.sender,
                    is_read=False
                )

            elif action == 'reject':
                friend_request.status = 'rejected'
                friend_request.save()

            # Đánh dấu thông báo lời mời kết bạn là đã đọc
            friend_request_notifications = Notification.objects.filter(
                sender=friend_request.sender,
                title='Lời mời kết bạn',
                usernotification__user=request.user
            )

            for notification in friend_request_notifications:
                user_notification = UserNotification.objects.get(
                    notification=notification,
                    user=request.user
                )
                user_notification.is_read = True
                user_notification.save()

            return JsonResponse({'status': 'success'})

        except Friend.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy lời mời kết bạn'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Phương thức không được hỗ trợ'})


@login_required
def unfriend(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin người dùng'})

        try:
            other_user = User.objects.get(id=user_id)

            # Tìm và xóa mối quan hệ bạn bè
            friend_relation = Friend.objects.filter(
                (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)),
                status='accepted'
            ).first()

            if friend_relation:
                friend_relation.delete()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Không tìm thấy mối quan hệ bạn bè'})

        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người dùng'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Phương thức không được hỗ trợ'})


@login_required
def get_friend_status(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)

        # Kiểm tra trạng thái bạn bè
        friend_relation = Friend.objects.filter(
            (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
        ).first()

        if not friend_relation:
            return JsonResponse({'status': 'not_friend'})

        if friend_relation.status == 'accepted':
            return JsonResponse({'status': 'friend'})

        if friend_relation.status == 'pending':
            if friend_relation.sender == request.user:
                return JsonResponse({'status': 'request_sent'})
            else:
                return JsonResponse({'status': 'request_received', 'request_id': friend_relation.id})

        return JsonResponse({'status': 'unknown'})

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người dùng'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
