from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female')]
    ROLE_CHOICES = [('admin', 'Admin'), ('user', 'User'), ('manager', 'Manager')]
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    avatar_url = models.URLField(max_length=255, blank=True, null=True)


class Department(models.Model):
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='departments_managed'
    )
    def __str__(self):
        return self.name

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    avatar_url = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    post = models.ForeignKey(Post,related_name='comments',  on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class GroupChat(models.Model):
    group_name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class GroupMember(models.Model):

    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Member')]
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

class Message(models.Model):
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)


class Friend(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('accepted', 'Đã chấp nhận'),
        ('rejected', 'Đã từ chối')
    ]
    sender = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')

class PrivateChat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def get_receiver(self, sender):
        return self.user2 if sender == self.user1 else self.user1

class PrivateMessage(models.Model):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(null=False, blank=False)
    sent_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed')]
    task_name = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='task_images/', null=True, blank=True)
    document = models.FileField(upload_to='task_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('task', 'user')

class TodoList(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):

    TYPE_CHOICES = [('company', 'Company'), ('personal', 'Personal')]
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.TextField()
    content = models.TextField()
    image = models.ImageField(upload_to='notification_images/', null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='personal')
    created_at = models.DateTimeField(auto_now_add=True)
    departments = models.ManyToManyField(Department, blank=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    is_global = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_global:
            self.departments.clear()

    def read_count(self):
        return self.usernotification_set.filter(
            is_read=True,
            user__is_staff=False,
            user__is_superuser=False
        ).count()

    def total_recipients(self):
        return self.usernotification_set.filter(
            user__is_staff=False,
            user__is_superuser=False
        ).count()


class UserNotification(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('notification', 'user')

class TaskProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ]

    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposals_made')
    to_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='proposals_received')
    title = models.CharField(max_length=255)
    description = models.TextField()
    document = models.FileField(upload_to='proposal_documents/', null=True, blank=True)
    image = models.ImageField(upload_to='proposal_images/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposals_reviewed')

    def __str__(self):
        return f"{self.title} -> {self.to_department.name}"


