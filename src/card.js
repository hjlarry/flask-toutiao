var $likeBtn = $('.like-button');
var $isLiked = $likeBtn.hasClass('liked');
console.log(123)
$likeBtn.on('click', (event) => {
    let $this = $(event.currentTarget);
    let url = $this.data('url');
    console.log(456)
    $.ajax({
        url: `/api/${url}`,
        type: $isLiked ? 'DELETE' : 'POST',
        data: {},
        success: function (rs) {
            if (!rs.r) {
                let isLiked = rs.data.is_liked;
                if ($isLiked != isLiked) {
                    $isLiked = isLiked;
                    $this.toggleClass('liked');
                }
            } else {
                alert('点赞失败，请稍后重试');
            }
        }
    });
})