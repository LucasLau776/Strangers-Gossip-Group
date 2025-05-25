// 点赞帖子
$(document).on("click", ".like-btn", function () {
  let postId = $(this).data("post-id");
  let btn = $(this);
  $.post("/like_post/", { post_id: postId }, function (data) {
    if (data.success) {
      btn.html("👍 " + data.like_count);
    }
  });
});

// 点赞评论
$(document).on("click", ".like-comment-btn", function () {
  let commentId = $(this).data("comment-id");
  let btn = $(this);
  $.post("/like_comment/", { comment_id: commentId }, function (data) {
    if (data.success) {
      btn.html("👍 " + data.like_count);
    }
  });
});

// 点赞回复
$(document).on("click", ".like-reply-btn", function () {
  let replyId = $(this).data("reply-id");
  let btn = $(this);
  $.post("/like_reply/", { reply_id: replyId }, function (data) {
    if (data.success) {
      btn.html("👍 " + data.like_count);
    }
  });
});

// 提交评论（支持图像）
$(document).on("submit", "#comment-form", function (e) {
  e.preventDefault();
  let formData = new FormData(this);
  $.ajax({
    url: "/add_comment/",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
});

// 提交回复（支持图像）
$(document).on("submit", ".reply-form", function (e) {
  e.preventDefault();
  let formData = new FormData(this);
  $.ajax({
    url: "/add_reply/",
    method: "POST",
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
      if (data.success) {
        location.reload();
      }
    }
  });
});

// 取消收藏
$(document).on("click", ".unsave-btn", function () {
  let postId = $(this).data("post-id");
  $.post("/unsave_post/", { post_id: postId }, function (data) {
    if (data.success) {
      $('#post-' + postId).remove();
    }
  });
});

// 举报提交（Ajax）
$(document).on("submit", "#report-form", function (e) {
  e.preventDefault();
  let formData = $(this).serialize();
  $.post("/report_post/", formData, function (data) {
    if (data.success) {
      alert("Report submitted successfully.");
      window.location.href = "/";
    } else {
      alert("Report failed.");
    }
  });
});

// 标记通知为已读
$(document).on("click", ".mark-read-btn", function (e) {
  e.preventDefault();
  let noteId = $(this).data("id");
  let btn = $(this);
  $.post("/mark_notification_read/" + noteId + "/", {}, function (data) {
    if (data.success) {
      btn.closest("li").css("font-weight", "normal");
      btn.remove();
    }
  });
});
