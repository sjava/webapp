$(function() {
    var path = location.pathname;
    var traffic = ['/', '/ports', '/olt_groups', '/olt_ports'];
    var xunjian = ['/sw_xunjian', '/olt_xunjian'];
    if ($.inArray(path, traffic) >= 0) {
        $("li:contains('流量')").addClass('active');
        return true
    } else if (path == '/bingfa') {
        $("li:contains('Bras并发')").addClass('active');
        return true
    } else if ($.inArray(path, xunjian) >= 0) {
        $("li:contains('设备巡检')").addClass('active');
        return true
    }
})
