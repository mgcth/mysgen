// Utils
function randomIntFromInterval(min,max) {
  return Math.floor(Math.random()*(max-min+1)+min);
}

// If Javascript enabled do some main navigation magic
function fadeInNav() {
  $("#nav li a").css({
    "display": "flex",
    "opacity": 0
  });
    $("#nav li a").css({
    "display": "-webkit-flex",
    "opacity": 0
  });

  navTimeIn = setTimeout(function() {// Delay (0) to separate display transition
    var navTime = 100;
    for (var i = 2; i <= $("#nav li").length; i++) {
      $("#nav li:nth-child(" + i + ") a").css({
        "opacity": 1,
        "transition": "opacity " + navTime + "ms"
        });
      navTime = navTime + 100;
    }
  }, 10)

  navOnMyWayOut = true;
}

function fadeOutNav() {
  var navTime = 600;
  for (var i = 2; i <= $("#nav li").length; i++) {
    $("#nav li:nth-child(" + i + ") a").css({
      "opacity": 0,
      "transition": "opacity " + navTime + "ms"
    });

    navTime = navTime - 100;
  }

  navTimeout = setTimeout(function() {
    $("#nav li a").css({
      "display": "none"
    });
    navKillTimeout = false;
  }, 600);

  navOnMyWayOut = false;
  navKillTimeout = true;
}

var navTimeout = 0;
var navOnMyWayOut = false;
var navKillTimeout = false;
$("#nav #menu-icon").on("click", function(e){
  if (navOnMyWayOut == false) {
    if (navKillTimeout == false) {
      fadeInNav();
    } else {
      clearTimeout(navTimeout);
      fadeInNav();
      navKillTimeout = false;
    }
  } else {
    fadeOutNav();
  }
});

$(document).on('click', function(e) {
  if (!$(e.target).closest('#nav').length) {
    fadeOutNav();
  }
});

// First hide it
// $(window).load(function() {
//   setTimeout(function(){
//     fadeOutNav();
//   }, 2000);
// });
// End the main navigation magic
// End Utils



//var loadedPages = [];
//var $div = $("<div>");
//for (var i = 1; i <= pages.length; i++) {
  //$div.load("https://mladen.gibanica.net/" + pages[i] + ".html #ajax_content_" + pages[i], function() {
  //  loadedPages[i-1] = $(this);
  //});
//}