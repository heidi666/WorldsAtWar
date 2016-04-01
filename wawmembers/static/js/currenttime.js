function PassTime(servertime){
    var list = servertime.split(':')
    var utc = new Date();
    utc.setUTCHours(list[0]);
    utc.setUTCMinutes(list[1]);
    utc.setUTCSeconds(list[2]);
    setInterval(function(){
        var seconds = utc.getUTCSeconds();
        utc.setUTCSeconds(seconds+1);
        var output = ("00" + utc.getUTCHours()).slice(-2) + ':' + ("00" + utc.getUTCMinutes()).slice(-2) + ':' + ("00" + utc.getUTCSeconds()).slice(-2);
        $('#datetime').html(output);
    }, 1000);
}
    
function LoadTime(){
    servertime = $('#datetime').html();
    PassTime(servertime);
    }
    
$(document).ready(LoadTime);