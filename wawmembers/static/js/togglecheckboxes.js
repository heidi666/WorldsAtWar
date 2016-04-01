$(document).ready(function(){
    $('#tickall').click(function(event) {
        event.preventDefault();
        $(':checkbox').prop('checked', true);
    });

    $('#untickall').click(function(event) {
        event.preventDefault();
        $(':checkbox').prop('checked', false);
    });
});