// 点赞帖子
$(document).on("click", ".like-btn", function () {
  let postId = $(this).data("post-id");
  let btn = $(this);
  $.post("/confession/like_post/", { post_id: postId }, function (data) {
    if (data.success) {
      btn.html("👍 Like (" + data.like_count + ")");
    }
  });
});

// 点赞评论
$(document).on("click", ".comment-like-btn", function () {
  let commentId = $(this).data("comment-id");
  let btn = $(this);
  $.post("/confession/like_comment/", { comment_id: commentId }, function (data) {
    if (data.success) {
      btn.html("👍 Like (" + data.like_count + ")");
    }
  });
});

// 收藏帖子（Save / Unsave Toggle）
$(document).on("click", ".save-btn", function () {
  const btn = $(this);
  const postId = btn.data("post-id");

  $.ajax({
    type: "POST",
    url: `/confession/toggle_save_post/${postId}/`,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest"  // ✅ 关键补上这一行
    },
    success: function (response) {
      if (response.success) {
        btn.html(response.saved ? "📌 Saved" : "📌 Save");
        btn.toggleClass("btn-outline-secondary btn-success");
      }
    },
    error: function () {
      alert("Failed to toggle save.");
    }
  });
});

// 取消收藏（Bookmark 页面）
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
        $("#post-" + postId).remove(); // 卡片移除
      }
    },
    error: function () {
      alert("Failed to unsave.");
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
    }
  });
});

// 提交回复
$(document).on("submit", ".reply-form", function (e) {
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