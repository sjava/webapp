$(function() {
    $("#myTabs a:first").tab("show");
    var infoModal = $('#myModal');
    $('.taskIP').on('click', function() {
        $.ajax({
            type: 'GET',
            url: '/task/' + $(this).data('id'),
            dataType: 'json',
            success: function(data) {
                task = data.task.split('\r\n')
                htmlData = ""
                $.each(task, function(i, v) {
                    htmlData += '<p>' + v + '</p>';
                });
                infoModal.find('.modal-body').html(htmlData);
                infoModal.modal('show');
            }
        });
        return false;
    });

    $('.myCheck').on('click', function() {
        $('#fakeLoader').fakeLoader({
            timeToHide: 1000 * 60 * 10
        });
        return true;
    });
})
