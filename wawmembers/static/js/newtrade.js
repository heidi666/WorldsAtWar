function Freightercalc() {

  var res = parseInt($('#offerres').val(), 10);
  var amount = parseInt($('#offeramount').val(), 10);
  var tradeno = parseInt($('#tradesamount').val(), 10);
  var hl = '<br>';
  var fr = ' freighters required per trade.';
  var frtot = ' freighters required in total.'
  var tot = null;

  if (res == 0 ||
    res == 11 ||
    res == 12 ||
    res == 13 ||
    res == 14 ||
    res == 15 ||
    res == 16 ||
    res == 17 ||
    res == 18 ||
    res == 19) {
    $('#resstat').html('No freighters required from you.' + hl);
    $('#amountstat').html('');
    $('#tradesstat').html('');
  }
  else {
    $('#resstat').html('Freighters will return in 1 hour if in the same sector, otherwise 2 hours.' + hl);
  }
  if (res == 1) {
    if (isNaN(amount)) {
      $('#amountstat').html('');
      $('#tradesstat').html('');
    }
    else {
      var quan = amount/200;
      if (amount%200 != 0) {
        quan += 1;
      }
      quan = Math.floor(quan);
      $('#amountstat').html(quan + fr + hl);
      if (!isNaN(tradeno)) {
        tot = quan * tradeno;
        $('#tradesstat').html(tot + frtot + hl);
      }
      else {
        $('#tradesstat').html('');
      }
    }
  }
  if (res == 2) {
    if (isNaN(amount)) {
      $('#amountstat').html('');
      $('#tradesstat').html('');
    }
    else {
      var quan = amount/20;
      if (amount%20 != 0) {
        quan += 1;
      }
      quan = Math.floor(quan);
      tot = quan * tradeno;
      $('#amountstat').html(quan + fr + hl);
      if (!isNaN(tradeno)) {
        tot = quan * tradeno;
        $('#tradesstat').html(tot + frtot + hl);
      }
      else {
        $('#tradesstat').html('');
      }
    }
  }
  if (res == 3) {
    if (isNaN(amount)) {
      $('#amountstat').html('');
      $('#tradesstat').html('');
    }
    else {
      var quan = amount/10;
      if (amount%10 != 0) {
        quan += 1;
      }
      quan = Math.floor(quan);
      tot = quan * tradeno;
      $('#amountstat').html(quan + fr + hl);
      if (!isNaN(tradeno)) {
        tot = quan * tradeno;
        $('#tradesstat').html(tot + frtot + hl);
      }
      else {
        $('#tradesstat').html('');
      }
    }
  }
  if (res == 4) {
    if (isNaN(amount)) {
      $('#amountstat').html('');
      $('#tradesstat').html('');
    }
    else {
      var quan = amount/2;
      if (amount%2 != 0) {
        quan += 1;
      }
      quan = Math.floor(quan);
      tot = quan * tradeno;
      $('#amountstat').html(quan + fr + hl);
      if (!isNaN(tradeno)) {
        tot = quan * tradeno;
        $('#tradesstat').html(tot + frtot + hl);
      }
      else {
        $('#tradesstat').html('');
      }
    }
  }
}

$(document).ready(function() {
  $('#offerres').change(function(){
    Freightercalc();
  });
  $('#offeramount').on("input", function(){
    Freightercalc();
  });
  $('#tradesamount').on("input", function(){
    Freightercalc();
  });
});