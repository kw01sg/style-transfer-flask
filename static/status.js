function send_post_request(url, success_callback, failure_callback) {
    $.ajax({
        type: 'POST',
        url: url,
        success: function (data, status) {
            if (data['state'] == 'SUCCESS') {
                update_progress_bar(100, data['elapsed_time']);
                success_callback();
            }
            if (data['state'] == 'PROGRESS') {
                progress = Math.floor(data['current'] * 100 / data['total']);
                update_progress_bar(progress, data['elapsed_time']);
            }
            failure_callback();
        },
        error: function () {
            alert('Unexpected error');
        }
    })
}


function update_progress_bar(progress, elapsed_time) {
    $('.progress-bar').text(progress + '%');
    $('.progress-bar').css('width', progress + '%');
    $('.progress-bar').attr('aria-valuenow', progress);
    $('#elapsed-time').text(elapsed_time);
}
