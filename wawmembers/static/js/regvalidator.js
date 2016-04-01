$(document).ready(function() {

    $('#id_username').change(function() {
        $.get('/ajax/username/', {username: $(this).val()},
			function(data){
				if(data == "True"){
					$("#userstatus").html("&nbsp;&nbsp;Username is available!").css("color", "green");
				} else {
					$('#userstatus').html("&nbsp;&nbsp;Username is not available!").css("color", "red");
				}
        });
    });

});