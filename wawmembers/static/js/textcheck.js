function Check(){
    var limit = $(this).attr('maxlength');
    var text = $(this).val();
    if (text.indexOf('<') != -1)
        $("#textcheckstatus").html('<br>Illegal character used! (<)').css("color", "red");
    else if (text.indexOf('>') != -1)
        $("#textcheckstatus").html('<br>Illegal character used! (>)').css("color", "red");
    else {
        $("#textcheckstatus").html('');
    }
}
    
$(document).ready(function(){
    $('.textcheck').on("input", function() {
        Check.apply(this);
    });
});