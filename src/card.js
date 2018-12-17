import './follow';
var $likeBtn = $('.like-button');
var $collectBtn = $('.collect-button');

var $isLiked = $likeBtn.hasClass('liked');
var $isCollected = $collectBtn.hasClass('collected');

$likeBtn.on('click', (event) => {
    let $this = $(event.currentTarget);
    let url = $this.data('url');
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
                    $this.find('span').text(rs.data.n_likes);
                    if (isLiked) {
                        $this.find('i').addClass('icon-liked').removeClass('icon-like');
                    } else {
                        $this.find('i').addClass('icon-like').removeClass('icon-liked');
                    }
                }
            } else {
                alert('点赞失败，请稍后重试');
            }
        }
    });
})

$collectBtn.on('click', (event) => {
    let $this = $(event.currentTarget);
    let url = $this.data('url');
    $.ajax({
        url: `/api/${url}`,
        type: $isCollected ? 'DELETE' : 'POST',
        data: {},
        success: function (rs) {
            if (!rs.r) {
                let isCollected = rs.data.is_collected;
                if ($isCollected != isCollected) {
                    $isCollected = isCollected;
                    $this.toggleClass('collected');
                    if (isCollected) {
                        $this.find('i').addClass('icon-collected').removeClass('icon-collect');
                    } else {
                        $this.find('i').addClass('icon-collect').removeClass('icon-collected');
                    }
                }
            } else {
                alert('收藏失败，请稍后重试');
            }
        }
    });
})