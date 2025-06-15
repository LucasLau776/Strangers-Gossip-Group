// ========================== Like, Save, Comment ==========================

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

// 点赞回复
$(document).on("click", ".like-reply-btn", function () {
  let replyId = $(this).data("reply-id");
  let btn = $(this);
  $.post("/confession/like_reply/", { reply_id: replyId }, function (data) {
    if (data.success) {
      btn.html("👍 Like (" + data.like_count + ")");
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

// 切换显示嵌套回复表单
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

// ✅ 提交 reply 表单
function submitReply(event, commentId) {
  event.preventDefault();
  const form = event.target;
  const content = form.querySelector("textarea[name='reply_content']").value;
  const parentReplyId = form.querySelector("input[name='parent_reply_id']")?.value || "";
  const image = form.querySelector("input[name='reply_image']")?.files[0];

  const formData = new FormData();
  formData.append("comment_id", commentId);
  formData.append("reply_content", content);
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

// 删除评论
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

// 删除回复
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

// 展开/隐藏 回复表单（点击 reply 按钮）
$(document).on("click", ".reply-btn", function () {
  const commentId = $(this).data("comment-id");
  $("#reply-form-" + commentId).toggle();
});
