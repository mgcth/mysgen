// Navigation.js
// Prevent from click to often
var isClicked = false;
var isPopstate = false;

// Create class linkState to save for html history and fill it with dummy data
var linkState = {item: whichPageActive, url: window.location.href};

// If no history event defined do this
if (typeof(history.replaceState) !== "undefined") {
  // Fill the linkState class
  linkState.item = whichPageActive;
  linkState.url = window.location.href;

  // Create the history event
  history.replaceState({
    item: linkState.item,
    url: linkState.url
  }, null, null);
}

// Set linkState (usually and update after internal link click)
function setLinkState(linkItem, menuUrl) {
  linkState.item = linkItem;
  linkState.url = menuUrl;
}

function doPushState(linkItem, menuUrl, poper) {
  var state = {item: linkItem, url: menuUrl},
  title = "",
  path  = menuUrl;

  if (whichPageActive != linkItem) {
    animatePage(linkItem);
    //hljs.initHighlightingOnLoad();
    //MathJax.Hub.Typeset();
    //fixPreWidth();

  } else {
    // A special function for the archives submenu, so that the menu itself is not reloaded
    if (pages[whichPageActive-1] == "archives") {
      $("#ajax_content_" + pages[linkItem-1] + " .ajax-fade").css({
        "opacity": 0,
        //"transform": "translateZ(0) rotateX(75deg)", // HW acceleration
        //"transform-origin": "50% bottom",
        "transition": "all " + 100 + "ms"
      });
    } else {
      $("#ajax_content_" + pages[linkItem-1]).css({
        "opacity": 0,
        "transform": "translateZ(0)", // HW acceleration
        "transition": "all " + animationPageDuration + "ms"
      });
    }
    setTimeout(function(){
      $("#page_" + pages[linkItem-1]).load(path + " .ajaxHook", function() {

        document.querySelectorAll('pre code').forEach((block) => {
          hljs.highlightBlock(block);
        });

        MathJax.Hub.Typeset();
        $(window).scrollTop(0);
      });
    }, 100);
  }

  // If a real link event, update history
  // In other words, if not popevent it is a real link
  if (poper == false) {
    history.pushState(state, null, path);
  }

  // Update linkState
  setLinkState(linkItem, menuUrl);
}

// If support for pushState exist
if (window.history && history.pushState) {
  // If click on menu link
  $("#nav").on("click", "a", function(e) {
    // Prevent default action
    e.preventDefault();

    // If no nearby previous event has been fired
    if (isClicked == false) {
      // Create variables to save
      var linkItem = whichPageActive;
      for (var i = 1; i <= pages.length; i++) {
        if ($(this).attr("title") == pages[i-1]) {
          linkItem = i;
        }
      }
      var menuUrl = $(this).attr("href");

      // Perform the loading and update history
      doPushState(linkItem, menuUrl, false);

      // Change clicked event
      isClicked = true;

      // Set the timeout
      setTimeout(function(){
        isClicked = false;
      }, animationPageDuration);
    }
  });

  // If click on link in main body
  $("#main").on('click', 'a', function(e) {
    if ($(this).attr("target") == "_blank") {
      // Do nothing for external links
    } else {
      // Prevent default action if internal link
      e.preventDefault();

      // If no nearby previous event has been fired
      if (isClicked == false) {
        // Create variables to save
        var linkItem = whichPageActive;
        var menuUrl = $(this).attr("href");

        // Perform the loading and update history
        doPushState(linkItem, menuUrl, false);

        // Change clicked event
        isClicked = true;

        // Set the timeout
        setTimeout(function(){
          isClicked = false;
        }, animationPageDuration);
      }
    }
  });
}

// If a history event is fired
$(window).on('popstate', function(e) {
  // Get the previous state
  var state = e.originalEvent.state;

  // If no nearby previous event has been fired
  if (isPopstate == false) {
    // Perform the loading and update history
    doPushState(state.item, state.url, true);

    // Change popstate so that no new event can be fired before a set time
    isPopstate = true;

    // Set the timeout
    popstateTimeout = setTimeout(function(){
      isPopstate = false;
    }, animationPageDuration);
  } else {
    // If the user browses very fast (too fast)

    // Change the popstate (not terribly important)
    isPopstate = false;

    // Clear timeout, run pushState again and cancel the new timeout too)
    clearTimeout(animationTimeout);
    doPushState(state.item, state.url, true);
    clearTimeout(animationTimeout);

    // These functions are in timeout and need to be run now when timeout is canceled
    $(hidePages).css({"display": "none"});
    $("html").removeClass("hide_scroll");
  }
});
// End Navigation.js
