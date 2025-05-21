document.addEventListener('DOMContentLoaded', function () {
    // Xử lý nút like
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function () {
            toggleLike(this);
        });
    });

    // Xử lý nút comment (hiện form nhập bình luận)
    document.querySelectorAll('.comment-button').forEach(button => {
        button.addEventListener('click', function () {
            toggleComment(this);
        });
    });

    // Xử lý nút hiện danh sách comment
    document.querySelectorAll('.comment-count-button').forEach(button => {
        button.addEventListener('click', function () {
            toggleCommentList(this);
        });
    });

    // Xử lý form report
    const reportForm = document.getElementById("report-form");
    if (reportForm) {
        reportForm.addEventListener("submit", function(event) {
            event.preventDefault();
            window.location.href = "/Trangchu.html";
        });
    }

    // Tìm kiếm người dùng
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsDiv = document.getElementById('search-results');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            searchUsers(this.value);
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', function () {
            const query = searchInput.value;
            searchUsers(query);
        });
    }

    function searchUsers(query) {
        if (!query.trim()) {
            resultsDiv.innerHTML = '';
            return;
        }

        fetch(`/search-users/?q=${encodeURIComponent(query)}`)
            .then(response => response.text())
            .then(html => {
                resultsDiv.innerHTML = html;
            })
            .catch(error => {
                console.error('Error fetching users:', error);
                resultsDiv.innerHTML = '<p>Có lỗi xảy ra khi tìm kiếm.</p>';
            });
    }
});

// Toggle form nhập bình luận
function toggleComment(button) {
    const post = button.closest('.post');
    const commentInput = post ? post.querySelector('.comment-input') : null;
    if (commentInput) {
        const isVisible = commentInput.style.display === 'flex';
        commentInput.style.display = isVisible ? 'none' : 'flex';
        button.classList.toggle('active', !isVisible);
    }
}

// Toggle danh sách bình luận
function toggleCommentList(btn) {
    const postElement = btn.closest('.post');
    const commentsList = postElement.querySelector('.comments-list');
    if (commentsList.style.display === 'none' || commentsList.style.display === '') {
        commentsList.style.display = 'block';
    } else {
        commentsList.style.display = 'none';
    }
}
