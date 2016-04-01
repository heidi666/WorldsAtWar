$(document).ready(function() {
    var prefs = $('#prefs').html();
    var array = prefs.split(',');
    for (var id in array) {
        $('#'+array[id]).prop('checked',true);
    }
});