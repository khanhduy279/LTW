document.addEventListener("DOMContentLoaded", () => {
  // Tab switching
  const postsTab = document.getElementById("posts-tab");
  const infoTab = document.getElementById("info-tab");
  const postsContent = document.getElementById("posts-content");
  const infoContent = document.getElementById("info-content");

  postsTab.addEventListener("click", () => {
    postsTab.classList.add("active");
    infoTab.classList.remove("active");
    postsContent.classList.remove("hidden");
    infoContent.classList.add("hidden");
  });

  infoTab.addEventListener("click", () => {
    infoTab.classList.add("active");
    postsTab.classList.remove("active");
    infoContent.classList.remove("hidden");
    postsContent.classList.add("hidden");
  });

  // Post menu dropdown
  const menuButtons = document.querySelectorAll(".menu-button");
  menuButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
      const dropdown = this.nextElementSibling;
      dropdown.classList.toggle("show");
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener("click", () => {
    const dropdowns = document.querySelectorAll(".dropdown-menu");
    dropdowns.forEach((dropdown) => {
      dropdown.classList.remove("show");
    });
  });

  // Edit post modal
  const editPostLinks = document.querySelectorAll(".edit-post");
  const editPostModal = document.getElementById("edit-post-modal");
  const closeModalButton = editPostModal.querySelector(".close-button");
  const textarea = editPostModal.querySelector(".post-textarea");
  const imagePreview = editPostModal.querySelector(".post-image-preview");
  const imageElement = imagePreview.querySelector("img");
  const postIdInput = editPostModal.querySelector("#edit-post-id");
  const avatarUrlInput = editPostModal.querySelector("#edit-post-image");
  const removeImageButton = editPostModal.querySelector(".remove-image-button");
  const addImageButton = document.getElementById("add-image-button");
  const newImageInput = document.getElementById("new-image-input");
  const editPostForm = document.getElementById("edit-post-form");

  editPostLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      const postId = link.getAttribute("data-post-id") || "";
      const title = link.getAttribute("data-post-title") || "";
      const imageUrl = link.getAttribute("data-post-image") || "";

      postIdInput.value = postId;
      textarea.value = title;

      if (imageUrl) {
        imagePreview.classList.remove("hidden");
        imageElement.src = imageUrl;
        avatarUrlInput.value = imageUrl;
      } else {
        imagePreview.classList.add("hidden");
        imageElement.src = "";
        avatarUrlInput.value = "";
      }

      editPostForm.action = `/edit_post/${postId}`;
      editPostModal.classList.add("show");
    });
  });

  closeModalButton.addEventListener("click", () => {
    editPostModal.classList.remove("show");
    textarea.value = "";
    imageElement.src = "";
    avatarUrlInput.value = "";
    imagePreview.classList.add("hidden");
  });

 if (removeImageButton) {
  removeImageButton.addEventListener("click", () => {
    imageElement.src = "";
    imagePreview.classList.add("hidden");
    avatarUrlInput.value = "";

    const removeImageInput = document.getElementById("remove-image-input");
    if (removeImageInput) {
      removeImageInput.value = "true";
    }
  });
}


  addImageButton.addEventListener("click", () => {
    newImageInput.click();
  });

 newImageInput.addEventListener("change", () => {
  const file = newImageInput.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      imageElement.src = e.target.result;
      imagePreview.classList.remove("hidden");
      avatarUrlInput.value = "";

      const removeImageInput = document.getElementById("remove-image-input");
      if (removeImageInput) {
        removeImageInput.value = "false";
      }
    };
    reader.readAsDataURL(file);
  }
});


  // Delete post modal
  const deleteLinks = document.querySelectorAll(".delete-post");
  const deleteModal = document.getElementById("confirm-delete-modal");
  const confirmDeleteYes = document.getElementById("confirm-delete-yes");
  const confirmDeleteNo = document.getElementById("confirm-delete-no");

  let postIdToDelete = null;
  let deleteUrlToUse = null;

  deleteLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      postIdToDelete = link.getAttribute("data-post-id");
      deleteUrlToUse = link.getAttribute("data-delete-url");
      deleteModal.style.display = "flex";
    });
  });

  confirmDeleteYes.addEventListener("click", () => {
    if (deleteUrlToUse) {
      window.location.href = deleteUrlToUse;
    }
  });

  confirmDeleteNo.addEventListener("click", () => {
    deleteModal.style.display = "none";
    postIdToDelete = null;
  });
});