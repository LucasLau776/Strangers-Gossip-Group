// ========================== Like, Save, Comment ==========================

// 点赞帖子
$(document).on("click", ".like-btn", function () {
  let postId = $(this).data("post-id");
  let btn = $(this);
  $.ajax({
    type: "POST",
    url: "/confession/like_post/",
    data: { post_id: postId },
    success: function (data) {
      if (data.success) {
        btn.html("👍 Like (" + data.like_count + ")");
      }
    },
    error: function (xhr) {
      if (xhr.status === 403) {
        alert("Error: You are banned from performing this action.");
      }
    }
  });
});

// 点赞评论
$(document).on("click", ".comment-like-btn", function () {
  let commentId = $(this).data("comment-id");
  let btn = $(this);
  $.ajax({
    type: "POST",
    url: "/confession/like_comment/",
    data: { comment_id: commentId },
    success: function (data) {
      if (data.success) {
        btn.html("👍 Like (" + data.like_count + ")");
      }
    },
    error: function (xhr) {
      if (xhr.status === 403) {
        alert("Error: You are banned from performing this action.");
      }
    }
  });
});

// 点赞帖子
$(document).on("click", ".reply-like-btn", function () {
  let replyId = $(this).data("reply-id");
  let btn = $(this);
  $.ajax({
    type: "POST",
    url: "/confession/like_reply/",
    data: { reply_id: replyId },
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        btn.html("👍 Like (" + data.like_count + ")");
      }
    },
    error: function (xhr) {
      if (xhr.status === 403 && xhr.responseJSON?.error === "You have been banned.") {
        alert("Error: You are banned from performing this action.");
      } else {
        alert("Failed to like reply.");
      }
    }
  });
});


// 收藏帖子
$(document).on("click", ".save-btn", function () {
  const btn = $(this);
  const postId = btn.data("post-id");
  $.ajax({
    type: "POST",
    url: `/confession/toggle_save_post/${postId}/`,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (response) {
      if (response.success) {
        btn.html(response.saved ? "📌 Saved" : "📌 Save");
        btn.toggleClass("btn-outline-secondary btn-success");
      }
    }
  });
});

// 取消收藏
$(document).on("click", ".unsave-btn", function () {
  const btn = $(this);
  const postId = btn.data("post-id");
  $.ajax({
    type: "POST",
    url: "/unsave_post/",
    data: { post_id: postId },
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        $("#post-" + postId).remove();
      }
    }
  });
});

// 提交评论
$(document).on("submit", "#comment-form", function (e) {
  e.preventDefault();
  let formData = new FormData(this);
  $.ajax({
    url: "/confession/add_comment/",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    },
    error: function (xhr) {
      const errMsg = xhr.responseJSON?.error || "";
      if (xhr.status === 403 && xhr.responseJSON?.error === "You have been banned.") {
        alert("Error: You are banned from performing this action.");
      } else {
        alert("Submission error. Please try again.");
      }
    }
  });
});

// 举报提交
$(document).on("submit", "#report-form", function (e) {
  e.preventDefault();
  let formData = $(this).serialize();
  $.ajax({
    url: window.location.pathname,
    method: "POST",
    data: formData,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        window.location.href = "/confession/done_report/";
      } else {
        alert("Report failed.");
      }
    },
    error: function () {
      alert("Failed to submit report.");
    }
  });
});

// 标记通知为已读
$(document).on("click", ".mark-read-btn", function (e) {
  e.preventDefault();
  let noteId = $(this).data("id");
  let btn = $(this);
  $.ajax({
    url: "/mark_notification_read/" + noteId + "/",
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        btn.closest("li").css("font-weight", "normal");
        btn.remove();
      }
    }
  });
});

// ========================== Reply-to-Reply ==========================

function toggleReplyForm(commentId, parentReplyId = null) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (form.style.display === "none") {
    form.style.display = "block";
    let input = form.querySelector("input[name='parent_reply_id']");
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = "parent_reply_id";
      form.appendChild(input);
    }
    input.value = parentReplyId || "";
  } else {
    form.style.display = "none";
  }
}

// ✅ 修正后的：提交 Reply 表单
function submitReply(event, commentId) {
  event.preventDefault();
  const form = event.target;
  const content = form.querySelector("textarea[name='reply_content']").value;
  const parentReplyId = form.querySelector("input[name='parent_reply_id']")?.value || "";
  const image = form.querySelector("input[name='reply_image']")?.files[0];

  const formData = new FormData();
  formData.append("comment_id", commentId);
  formData.append("reply_content", content);  // ✅ 修复字段名
  if (parentReplyId) formData.append("parent_reply_id", parentReplyId);
  if (image) formData.append("image", image);

  $.ajax({
    url: "/confession/add_reply/",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
}

function deleteComment(commentId) {
  if (!confirm("Are you sure you want to delete this comment?")) return;

  $.ajax({
    url: `/confession/comment/delete/${commentId}/`,
    type: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
}

function deleteReply(replyId) {
  if (!confirm("Are you sure you want to delete this reply?")) return;

  $.ajax({
    url: `/confession/reply/delete/${replyId}/`,
    type: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
}

// 获取 CSRF Token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// reply-form 提交 Ajax
$(document).on("submit", ".reply-submit-form", function (e) {
  e.preventDefault();
  let formData = new FormData(this);
  $.ajax({
    url: "/confession/add_reply/",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"
    },
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
});

// 展开/隐藏 回复表单
$(document).on("click", ".reply-btn", function () {
  const commentId = $(this).data("comment-id");
  $("#reply-form-" + commentId).toggle();
});

// 提交 Reply 表单
$(document).on("submit", ".reply-submit-form", function (e) {
  e.preventDefault();

  const commentId = $(this).data("comment-id");
  const content = $(this).find("textarea[name='reply_content']").val();
  const csrfToken = $(this).find("[name='csrfmiddlewaretoken']").val();

  if (!content.trim()) {
    alert("Reply cannot be empty.");
    return;
  }

  $.ajax({
    url: "/confession/add_reply/",
    method: "POST",
    data: {
      comment_id: commentId,
      content: content,
      csrfmiddlewaretoken: csrfToken,
    },
    success: function () {
      location.reload(); // 成功后刷新页面显示新回复
    },
    error: function () {
      alert("Failed to post reply.");
    }
  });
});

$(document).on("click", ".delete-post", function () {
    if (confirm("Are you sure you want to delete this post?")) {
        const postId = $(this).data("post-id");
        $.ajax({
            url: `/confession/post/delete/${postId}/`,
            method: "POST",
            data: {
                csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
            },
            success: function () {
                alert("Post deleted successfully");
                window.location.href = "/";
            },
            error: function (xhr) {
                alert(xhr.responseJSON.error || "Failed to delete post");
            },
        });
    }
});

$(document).on("click", ".delete-comment", function () {
    if (confirm("Are you sure you want to delete this comment?")) {
        const commentId = $(this).data("comment-id");
        $.ajax({
            url: `/confession/comment/delete/${commentId}/`,
            method: "POST",
            data: {
                csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
            },
            success: function () {
                alert("Comment deleted successfully");
                location.reload();
            },
            error: function (xhr) {
                alert(xhr.responseJSON.error || "Failed to delete comment");
            },
        });
    }
});

$(document).on("click", ".delete-reply", function () {
    if (confirm("Are you sure you want to delete this reply?")) {
        const replyId = $(this).data("reply-id");
        $.ajax({
            url: `/confession/reply/delete/${replyId}/`,
            method: "POST",
            data: {
                csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
            },
            success: function () {
                alert("Reply deleted successfully");
                location.reload();
            },
            error: function (xhr) {
                alert(xhr.responseJSON.error || "Failed to delete reply");
            },
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
  const postForm = document.querySelector("#post-form");
  const submitBtn = document.querySelector("#submit-post-btn");

  if (postForm && submitBtn) {
    postForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(postForm);

      fetch("/confession/ajax_post_confession/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
        },
        body: formData,
      })
        .then((response) => {
          if (handleBanError(response)) return;
          return response.json();
        })
        .then((data) => {
          if (!data) return;
          
          if (data.cooldown) {
            alert(`Please wait ${data.seconds_left} seconds before posting again.`);
          } else if (data.success) {
            alert("Post submitted successfully!");
            postForm.reset();
          } else {
            alert(data.error || "Failed to post.");
          }
        })
        .catch((error) => {
          console.error("Error submitting post:", error);
          alert("An error occurred.");
        });
    });
  }
});

// ===== Moderation Panel: Dismiss Button AJAX =====
document.addEventListener("DOMContentLoaded", function () {
  const dismissButtons = document.querySelectorAll(".dismiss-button");
  dismissButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const contentType = btn.dataset.type; // "post" or "comment"
      const objectId = btn.dataset.id;

      fetch(`/moderation/dismiss/${contentType}/${objectId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ remove: false }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            // ✅ 立即移除该元素
            const container = btn.closest(".report-card");
            if (container) container.remove();
          } else {
            alert("Dismiss failed: " + (data.error || "unknown error"));
          }
        })
        .catch((err) => {
          console.error("Dismiss error", err);
          alert("Failed to dismiss. See console.");
        });
    });
  });
});


// 没有 getCSRFToken 函数，可以
function getCSRFToken() {
  const cookieValue = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  return cookieValue ? cookieValue.split("=")[1] : "";
}

// ==== Handle Global Ban Error Responses ====
function handleBanError(response) {
  if (response.status === 403) {
    response.json().then((data) => {
      alert(data.error || "You are banned from this action.");
    });
    return true;
  }
  return false;
}
