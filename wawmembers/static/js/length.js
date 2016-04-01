function Length(){
    var id = $(this).attr('id');
    var limit = $(this).attr('maxlength');
    var len = $(this).val().length;
    if (len <= limit){
        $("#"+id+"status").html((limit-len) + ' chars left.').css("color", "white");
    }
    else {
        $("#"+id+"status").html((len-limit) + ' chars over!').css("color", "red");
    }
}

$(document).ready(function(){
    $('.countable').on("input", function() {
        Length.apply(this);
    });
});