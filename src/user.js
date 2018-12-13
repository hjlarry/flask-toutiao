import './scss/user.scss';
import './follow';


$('#user-tab a').on('click', (event) => {
    event.preventDefault()
    let $this = $(event.currentTarget);
    let url = $this.data('url');
    window.location.replace(url);
})