
function Uncheck(selected,other) {
  if ($(selected).prop('checked') == true) {
    $(other).prop('checked',false)
  }
  else if ($(selected).prop('checked') == false) {
    $(other).prop('checked',true)
  }
}

function FlagShipDesc(shiptype) {
  if (shiptype == 1) {
    $('#shipdesc').html('A personal fighter is light and nimble, perfect for bloodthirsty or thrill-seeking <br> leaders ' + 
      'who like to get up close to the action and inflict some damage.')
  }
  else if (shiptype == 2) {
    $('#shipdesc').html('A militarised yacht - while reasonably well-armed - is replete with comforts, <br> suitable for those leaders ' +
      'who like luxury even in the midst of battle.')
  }
  else if (shiptype == 3) {
    $('#shipdesc').html('A command ship is well armored and bristling with comms equipment, <br> suitable for those leaders ' +
      'who plan every move and stay on top of their fleet.')
  }
}


function Fuelcalc(type) {
  toadd = ''
  if (type == '#mothball') {
    toadd = ' for reactivation'
  }
  var shiptype = parseInt($(type+'ship').val(), 10);
  var amount = parseInt($(type+'amount').val(), 10);
  if (shiptype == 1) {
    var fuel = amount;
  }
  else if (shiptype == 2) {
    var fuel = 2*amount;
  }
  else if (shiptype == 3) {
    var fuel = 3*amount;
  }
  else if (shiptype == 4) {
    var fuel = 4*amount;
  }
  else if (shiptype == 5) {
    var fuel = 5*amount;
  }
  else if (shiptype == 6) {
    var fuel = 6*amount;
  }
  else if (shiptype == 7) {
    var fuel = 8*amount;
  }
  else if (shiptype == 8) {
    var fuel = 10*amount;
  }
  else if (shiptype == 9) {
    var fuel = 15*amount;
  }
  else if (shiptype == 10) {
    var fuel = 10;
  }
  if (isNaN(fuel) == false) {
    fuel = Math.floor((fuel/2) + 0.5);
    $(type+'cost').html('Cost: ' + fuel + ' warpfuel' + toadd);
  }
  else {
    $(type+'cost').html('');
  }
}

$(document).ready(function(){

  $("#plusstage").submit(function(event) {
    if(!confirm("Are you sure you want to stage all your ships?")) {
      event.preventDefault();
    }
  });

  $("#minusstage").submit(function(event) {
    if(!confirm("Are you sure you want to unstage all your ships?")) {
      event.preventDefault();
    }
  });

  $("#scuttleflagship").submit(function(event) {
    if(!confirm("Are you sure you want to scuttle your flagship?")) {
      event.preventDefault();
    }
  });

  $("#buildallships").submit(function(event) {
    var list = [$('#amountfig').val(), $('#amountcor').val(), $('#amountlcr').val(), $('#amountdes').val(), $('#amountfri').val(), 
      $('#amounthcr').val(), $('#amountbcr').val(), $('#amountbsh').val(), $('#amountdre').val()];
    var toreturn = list.join();
    var value = $("<input>", { type: "hidden", name: "buildquantities", value: toreturn }); 
    $('#buildallships').append($(value));
  });
  
  $('#prodhome').change(function(){
      Uncheck('#prodhome','#prodstaging');
  });
  $('#prodstaging').change(function(){
      Uncheck('#prodstaging','#prodhome');
  });
  $('#sendhome').change(function(){
      Uncheck('#sendhome','#sendstaging');
  });
  $('#sendstaging').change(function(){
      Uncheck('#sendstaging','#sendhome');
  });
  $('#receivehome').change(function(){
      Uncheck('#receivehome','#receivestaging');
  });
  $('#receivestaging').change(function(){
      Uncheck('#receivestaging','#receivehome');
  });
    
  $('#shipmoveship').change(function(){
      Fuelcalc('#shipmove');
  });
  $('#shipmoveamount').on("input", function(){
      Fuelcalc('#shipmove');
  });
  $('#mothballship').change(function(){
      Fuelcalc('#mothball');
  });
  $('#mothballamount').on("input", function(){
      Fuelcalc('#mothball');
  });

  $('#flagshipselect').change(function(){
      FlagShipDesc($(this).val());
  });

});