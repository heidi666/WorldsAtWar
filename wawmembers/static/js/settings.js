$(document).ready(function() {

    $('#flagchoice').change(function() {
        $.get('/ajax/flag/', {id: $(this).val()},
            function(data){
                $("#selectflag").html('<img src="' + data + '" alt="flag" class="selectdisplay">');
        });
    });

    $('#avatarchoice').change(function() {
        $.get('/ajax/avatar/', {id: $(this).val()},
            function(data){
                $("#selectavatar").html('<img src="' + data + '" alt="avatar" class="selectdisplay">');
        });
    });

    $('#bgchoice').change(function() {
        $.get('/ajax/background/', {id: $(this).val()},
            function(data){
                $("#selectbg").html('<img src="' + data + '" alt="background" class="selectdisplay">');
        });
    });

    $('#pspicchoice').change(function() {
        $.get('/ajax/personalship/', {id: $(this).val()},
            function(data){
                $("#selectps").html('<img src="' + data + '" alt="psship" class="selectdisplay">');
        });
    });

    $('#sortselect').change(function() {
        var select = $(this).val();
        $('#sortselect').val(select);
        var input = $("<input>", { type: "hidden", name: "selectsort" });
        $('#sortform').append($(input));
        $('#sortform').submit();
    });

    $('#policyselect').change(function() {
        var select = $(this).val();
        $('#policyselect').val(select);
        var input = $("<input>", { type: "hidden", name: "selectpolicy" });
        $('#policyform').append($(input));
        $('#policyform').submit();
    });

    $('#buildselect').change(function() {
        var select = $(this).val();
        $('#buildselect').val(select);
        var input = $("<input>", { type: "hidden", name: "selectship" });
        $('#shipform').append($(input));
        $('#shipform').submit();
    });

    $('#flagselect').change(function() {
        var select = $(this).val();
        $('#flagselect').val(select);
        var input = $("<input>", { type: "hidden", name: "selectflagpref" });
        $('#flagform').append($(input));
        $('#flagform').submit();
    });

});