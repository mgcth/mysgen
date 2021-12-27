// Animation.js
// Set the transition time
var animationPageDuration = 250;
var animationTimeout;
var hidePages = [""];

// Set the z displacement
var zDisplacement = 100;

// Number of pages
var pageCount = $("#main .page").length;

// Function to animate the frame transitions
function animatePage(whichFrame) {

  $("html").addClass("hide_scroll");

  whichPageActive = whichFrame;

  var hideCounter = 0;
  var hide = [""];

  for (var j = 1; j <= pageCount; j++) {
    if (whichFrame == j) {

      $("#page_" + pages[j-1]).css({"display": "block", "z-index": 0});

      if ($("#page_" + pages[j-1] + ":visible").length == 0) {
        $("#page_" + pages[j-1]).delay(0).queue( function(next){
          $(this).css({
            "opacity": 1,
            "transform": "translateX(0) translateY(0) translateZ(0)",
            "transition": "all " + animationPageDuration + "ms",
          });
          next();
        });

      } else {
        $("#page_" + pages[j-1]).delay(0).queue( function(next){
          $(this).css({
            "opacity": 1,
            "transform": "translateX(0) translateY(0) translateZ(0)",
            "transition": "all " + animationPageDuration + "ms"
          });
          next();
        });
      }

      $("#nav ul li a").removeClass("activeMenu");
      $("#nav ul li:nth-child(" + (whichFrame+1) + ") a").addClass("activeMenu");

    } else if (whichFrame > j) {
      $("#page_" + pages[j-1]).css({
        "opacity": 0,
        "transform": "translateX(0) translateY(0) translateZ(" + zDisplacement * (whichFrame - j) + "px)",
        "transition": "all " + animationPageDuration + "ms"
      });

      $("#page_" + pages[j-1]).css({"z-index": -whichFrame + j -1});

      hide[hideCounter] = "#page_" + pages[j-1];
      hideCounter++;

    } else {
      var opacityValue = 1 / (j - whichFrame) * 0.1;
      if ($("#main .page:nth-child(" + j + "):visible").length == 0) {
        $("#page_" + pages[j-1]).css({
          "opacity": opacityValue,
          "transform": "translateX(0) translateY(0) translateZ(" + zDisplacement * (whichFrame - j) + "px)",
          "transition": "all " + animationPageDuration + "ms"
        });

      } else {
        $("#page_" + pages[j-1]).css({
          "opacity": opacityValue,
          "transform": "translateX(0) translateY(0) translateZ(" + zDisplacement * (whichFrame - j) + "px)",
          "transition": "all " + animationPageDuration + "ms"
        });
      }

      $("#page_" + pages[j-1]).css({"z-index": -(j-1+1)});

      //$("#page_" + pages[j-1]).css({"display": "block"});
      hide[hideCounter] = "#page_" + pages[j-1];
      hideCounter++;
    }
  }

  hidePages = hide.join(", ");

  animationTimeout = setTimeout(function() {
    $(hidePages).css({"display": "none"});
    $("html").removeClass("hide_scroll");
  }, animationPageDuration);
}
// End Animation.js
