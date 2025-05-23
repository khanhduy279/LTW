{% extends 'mxh/base.html' %}
{% load static %}

{% block title %}Thông báo cá nhân{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'mxh/styles/notification.css' %}">
<style>
  .friend-response-buttons {
    display: flex;
    gap: 10px;
    margin-top: 10px;
  }

  .accept-btn, .reject-btn {
    padding: 5px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
  }

  .accept-btn {
    background-color: #4CAF50;
    color: white;
  }

  .reject-btn {
    background-color: #f44336;
    color: white;
  }

  .accept-btn:hover {
    background-color: #45a049;
  }

  .reject-btn:hover {
    background-color: #d32f2f;
  }

  .friend-request-notification {
    border-left: 3px solid #4CAF50;
  }

  .read {
    opacity: 0.7;
  }

  .unread {
    background-color: #f0f8ff;
  }
</style>
{% endblock %}

{% block content %}
<div class="container">
  <div class="notification-container">
    <div class="notification-header">
      <h2>Thông báo cá nhân</h2>
    </div>

    <div class="notification-tabs">
      <a href="{% url 'notification_company' %}" class="tab">Công ty</a>
      <a href="{% url 'notification_personal' %}" class="tab active">Cá nhân</a>
    </div>

    <div class="notification-content">
      <div id="personal-content">
        {% for notification in personal_notifications %}
        <div class="profile {% if notification.is_read %}read{% else %}unread{% endif %} {% if 'Lời mời kết bạn' in notification.title %}friend-request-notification{% endif %}" data-notification-id="{{ notification.id }}">
          <div class="avatar">
            {% if notification.sender and notification.sender.avatar_url %}
            <img src="{{ notification.sender.avatar_url }}" alt="Avatar" class="avatar-img">
            {% else %}
            <img src="{% static 'mxh/images/default_avatar.png' %}" alt="Avatar mặc định" class="avatar-img">
            {% endif %}
          </div>

          <div class="info">
            <p class="name">{{ notification.sender.username }}</p>
            <p class="content">{{ notification.content }}</p>

            {% if 'Lời mời kết bạn' in notification.title and not notification.is_read %}
              {% with friend_request=notification.sender.friend_requests_sent.all|first %}
                {% if friend_request %}
                <div class="friend-response-buttons">
                  <button class="accept-btn" data-request-id="{{ friend_request.id }}">Đồng ý</button>
                  <button class="reject-btn" data-request-id="{{ friend_request.id }}">Từ chối</button>
                </div>
                {% endif %}
              {% endwith %}
            {% endif %}
          </div>
          <p class="time">{{ notification.created_at|date:'d/m/Y H:i' }}</p>
        </div>
        {% empty %}
        <div class="empty-notification">
          <p>Không có thông báo cá nhân nào.</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'mxh/script/friends.js' %}"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Đánh dấu thông báo đã đọc khi người dùng xem
    const unreadNotifications = document.querySelectorAll('.unread');
    unreadNotifications.forEach(notification => {
      const notificationId = notification.dataset.notificationId;

      // Gửi request để đánh dấu thông báo đã đọc
      fetch(`/mark-notification-as-read/${notificationId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        }
      });
    });

    // Xử lý nút đồng ý và từ chối lời mời kết bạn
    const acceptButtons = document.querySelectorAll('.accept-btn');
    const rejectButtons = document.querySelectorAll('.reject-btn');

    acceptButtons.forEach(button => {
      button.addEventListener('click', function() {
        const requestId = this.dataset.requestId;
        respondToFriendRequest(requestId, 'accept');
      });
    });

    rejectButtons.forEach(button => {
      button.addEventListener('click', function() {
        const requestId = this.dataset.requestId;
        respondToFriendRequest(requestId, 'reject');
      });
    });

    // Hàm lấy CSRF token từ cookie
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }

    // Hàm xử lý phản hồi lời mời kết bạn
    function respondToFriendRequest(requestId, action) {
      fetch(`/respond-friend-request/${requestId}/${action}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        if (response.ok) {
          // Tìm và xóa thông báo khỏi giao diện
          const notification = document.querySelector(`.friend-request-notification button[data-request-id="${requestId}"]`).closest('.profile');
          if (notification) {
            notification.remove();

            // Cập nhật số lượng thông báo
            const notificationCount = document.querySelector('.notification-count');
            if (notificationCount) {
              const currentCount = parseInt(notificationCount.textContent);
              if (currentCount > 0) {
                notificationCount.textContent = currentCount - 1;
                if (currentCount - 1 === 0) {
                  notificationCount.style.display = 'none';
                }
              }
            }
          }
        }
      })
      .catch(error => {
        console.error('Lỗi khi phản hồi lời mời kết bạn:', error);
      });
    }
  });
</script>
{% endblock %}
