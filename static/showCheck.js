$(function() {
    $("#myTabs a:first").tab("show");

    var $tr = $("#ports tbody tr");
    $tr.each(function() {
        var desc = $(this).children("td:eq(1)").text().toLowerCase();
        var state = $(this).children("td:eq(2)").text().toLowerCase();
        if (desc != 'none' && state != 'up') {
            $(this).css("background-color", "yellow");
        }
    })

})
