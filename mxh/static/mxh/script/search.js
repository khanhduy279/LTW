document.addEventListener("DOMContentLoaded", () => {
  // Xử lý hiển thị kết quả tìm kiếm
  const searchInput = document.getElementById("search-input")
  const searchResultsPopup = document.getElementById("search-results-popup")

  if (searchInput) {
    searchInput.addEventListener("focus", () => {
      if (searchResultsPopup) {
        searchResultsPopup.style.display = "block"
      }
    })

    // Hiển thị kết quả khi nhập
    searchInput.addEventListener("input", function () {
      if (this.value.trim() !== "") {
        fetchSearchResults(this.value)
      } else {
        if (searchResultsPopup) {
          searchResultsPopup.style.display = "none"
        }
      }
    })

    // Đóng kết quả khi click ra ngoài
    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !searchResultsPopup.contains(e.target)) {
        searchResultsPopup.style.display = "none"
      }
    })
  }

  // Xử lý các nút kết bạn
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("friend-btn")) {
      const userId = e.target.dataset.userId
      const action = e.target.dataset.action

      if (action === "send-request") {
        sendFriendRequest(userId, e.target)
      } else if (action === "cancel-request") {
        cancelFriendRequest(userId, e.target)
      } else if (action === "unfriend") {
        unfriend(userId, e.target)
      } else if (action === "respond-request") {
        const requestId = e.target.dataset.requestId
        showRespondModal(requestId)
      }
    }
  })

  // Cập nhật trạng thái nút kết bạn
  updateFriendButtons()
})

// Lấy kết quả tìm kiếm
function fetchSearchResults(query) {
  fetch(`/search-employees/?q=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      const searchResultsPopup = document.getElementById("search-results-popup")
      if (searchResultsPopup) {
        searchResultsPopup.innerHTML = ""

        if (data.users && data.users.length > 0) {
          data.users.forEach((user) => {
            const resultItem = document.createElement("div")
            resultItem.className = "search-result-item"

            const userInfo = document.createElement("div")
            userInfo.className = "user-info"

            const avatar = document.createElement("div")
            avatar.className = "avatar"

            if (user.avatar_url) {
              const img = document.createElement("img")
              img.src = user.avatar_url
              img.alt = user.username
              avatar.appendChild(img)
            } else {
              const defaultAvatar = document.createElement("div")
              defaultAvatar.className = "default-avatar"
              defaultAvatar.textContent =
                user.first_name.charAt(0).toUpperCase() + user.last_name.charAt(0).toUpperCase()
              avatar.appendChild(defaultAvatar)
            }

            const userName = document.createElement("div")
            userName.className = "user-name"
            userName.textContent = user.first_name + " " + user.last_name

            userInfo.appendChild(avatar)
            userInfo.appendChild(userName)

            const friendBtn = document.createElement("button")
            friendBtn.className = "friend-btn btn-primary"
            friendBtn.dataset.userId = user.id
            friendBtn.dataset.action = "send-request"
            friendBtn.textContent = "Kết bạn"

            resultItem.appendChild(userInfo)
            resultItem.appendChild(friendBtn)

            searchResultsPopup.appendChild(resultItem)
          })

          const viewAll = document.createElement("div")
          viewAll.className = "view-all"
          const viewAllLink = document.createElement("a")
          viewAllLink.href = "#"
          viewAllLink.textContent = "Xem tất cả"
          viewAll.appendChild(viewAllLink)
          searchResultsPopup.appendChild(viewAll)
        } else {
          const noResults = document.createElement("div")
          noResults.className = "no-results"
          noResults.textContent = "Không tìm thấy nhân viên!"
          searchResultsPopup.appendChild(noResults)
        }

        searchResultsPopup.style.display = "block"
        updateFriendButtons()
      }
    })
    .catch((error) => {
      console.error("Error fetching search results:", error)
    })
}

// Cập nhật trạng thái nút kết bạn
function updateFriendButtons() {
  const friendButtons = document.querySelectorAll(".friend-btn")

  friendButtons.forEach((button) => {
    const userId = button.dataset.userId

    fetch(`/get-friend-status/${userId}/`)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "friend") {
          button.textContent = "Hủy kết bạn"
          button.dataset.action = "unfriend"
          button.classList.remove("btn-primary", "btn-secondary")
          button.classList.add("btn-danger")
        } else if (data.status === "request_sent") {
          button.textContent = "Hủy lời mời"
          button.dataset.action = "cancel-request"
          button.classList.remove("btn-primary", "btn-danger")
          button.classList.add("btn-secondary")
        } else if (data.status === "request_received") {
          button.textContent = "Phản hồi"
          button.dataset.action = "respond-request"
          button.dataset.requestId = data.request_id
          button.classList.remove("btn-danger", "btn-secondary")
          button.classList.add("btn-primary")
        } else {
          button.textContent = "Kết bạn"
          button.dataset.action = "send-request"
          button.classList.remove("btn-danger", "btn-secondary")
          button.classList.add("btn-primary")
        }
      })
      .catch((error) => {
        console.error("Error fetching friend status:", error)
      })
  })
}

// Gửi lời mời kết bạn
function sendFriendRequest(userId, button) {
  const formData = new FormData()
  formData.append("user_id", userId)

  fetch("/send-friend-request/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        button.textContent = "Hủy lời mời"
        button.dataset.action = "cancel-request"
        button.classList.remove("btn-primary", "btn-danger")
        button.classList.add("btn-secondary")
      } else {
        alert(data.message || "Có lỗi xảy ra")
      }
    })
    .catch((error) => {
      console.error("Error sending friend request:", error)
    })
}

// Hủy lời mời kết bạn
function cancelFriendRequest(userId, button) {
  const formData = new FormData()
  formData.append("user_id", userId)

  fetch("/cancel-friend-request/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        button.textContent = "Kết bạn"
        button.dataset.action = "send-request"
        button.classList.remove("btn-danger", "btn-secondary")
        button.classList.add("btn-primary")
      } else {
        alert(data.message || "Có lỗi xảy ra")
      }
    })
    .catch((error) => {
      console.error("Error canceling friend request:", error)
    })
}

// Hủy kết bạn
function unfriend(userId, button) {
  const formData = new FormData()
  formData.append("user_id", userId)

  fetch("/unfriend/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        button.textContent = "Kết bạn"
        button.dataset.action = "send-request"
        button.classList.remove("btn-danger", "btn-secondary")
        button.classList.add("btn-primary")
      } else {
        alert(data.message || "Có lỗi xảy ra")
      }
    })
    .catch((error) => {
      console.error("Error unfriending:", error)
    })
}

// Phản hồi lời mời kết bạn
function showRespondModal(requestId) {
  const confirmed = confirm("Bạn muốn chấp nhận lời mời kết bạn? (OK: Đồng ý, Cancel: Từ chối)")
  const action = confirmed ? "accept" : "reject"

  const formData = new FormData()
  formData.append("request_id", requestId)
  formData.append("action", action)

  fetch("/respond-friend-request/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        updateFriendButtons()
      } else {
        alert(data.message || "Có lỗi xảy ra")
      }
    })
    .catch((error) => {
      console.error("Error responding to friend request:", error)
    })
}

// Lấy CSRF token từ cookie
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}
