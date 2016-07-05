$(function() {
    $("#myTabs a:first").tab("show");

    var $tr = $("#ports tbody tr");
    $tr.each(function() {
        var desc = $(this).children("td:eq(1)").text().toLowerCase();
        var state = $(this).children("td:eq(2)").text().toLowerCase();
        if (desc != 'none' && state != 'up') {
            $(this).css("background-color", "yellow");
        }
    });

    var $tr1 = $("#vlans tbody tr");
    $tr1.each(function() {
        var vlan = parseInt($(this).children("td:eq(0)").text());
        var user1 = parseInt($(this).children("td:eq(1)").text());
        var user2 = $(this).children("td:eq(2)").text();
        if (user2 == "not find") {
            $(this).css("background-color", "red");
            return true
        }
        user2 = parseInt(user2);
        if (user1 == user2) {
            $(this).css("background-color", "#00FF00");
        } else if ((vlan == 48 || vlan == 49 || vlan == 50) && user1 > user2) {
            $(this).css("background-color", "red");
        } else if (user2 > 0) {
            $(this).css("background-color", "#00FF00")
        } else {
            $(this).css("background-color", "yellow")
        }
    })

})
