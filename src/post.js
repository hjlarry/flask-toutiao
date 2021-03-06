import "./scss/post.scss";

import './card';
import {
    SimpleShare
} from "./simple-share";

var $comments = $('#comments');
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

var share = new SimpleShare({
    url: $('meta[name="url"]').attr('content'),
    title: $('.social-share-button').data('title'),
    content: $('meta[name="content"]').attr('content')
    // pic: ''
});

$('.share-weibo').on('click', (event) => {
    event.preventDefault();
    share.weibo();
});

$('.share-weixin').on('click', (event) => {
    event.preventDefault();
    share.weixin();
});