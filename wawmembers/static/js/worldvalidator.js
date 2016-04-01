function CheckWorld(){
    $.get('/ajax/worldname', {worldname: $("#id_worldname").val()},
        function(data){
            if(data == "True"){
                $("#worldstatus").html("<br>World name is available!").css("color", "green");
            } else {
                $('#worldstatus').html("<br>World name is not available!").css("color", "red");
            }
        });
    }
    
function onWorldChange(){
        $("#id_worldname").change(function(){CheckWorld()});
    }
    
$(document).ready(onWorldChange);