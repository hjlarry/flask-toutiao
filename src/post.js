import "./scss/post.scss";

import './card';

var $comments = $('#comments');
var $submitBtn = $('#comment-submit');
var $commentForm = $('#comment-form');

$commentForm.on('submit', (event) => {
    event.preventDefault();
    let $this = $(event.currentTarget);
    let $content = $this.find('#comment-content');
    let url = $this.data('url');

    $.ajax({
        url: `/api/${url}`,
        type: 'POST',
        data: {
            content: $content.val()
        },
        success: function (rs) {
            if (!rs.r) {
                $content.val(''); // 清空textarea
                $(rs.data.html).hide().prependTo($comments).fadeIn(1000);
            } else {
                alert('评论失败, 请稍后再试');
            }
        }
    });
    return false;
});