$(function() {
    var nav = $('nav');
    var navWrapper = $('.nav-wrapper');
    var waypointOffset = 30;
    navWrapper.waypoint({
        handler: function(direction) {
            if (direction == 'down') {
                navWrapper.css({ 'height': nav.outerHeight() });
                nav.addClass('sticky');
            } else {
                navWrapper.css({ 'height': 'auto' });
                nav.removeClass('sticky');
            }
        },
        offset: waypointOffset
    });

    var sections = $('article');
    var navLinks = $('nav a');
    sections.waypoint({
        handler: function(direction) {
            var activeSection = $(this);
            if (direction == 'up') {
                activeSection = activeSection.prev();
            }
            var activeLink = $('nav a[href="#' + activeSection.attr("id") + '"]');
            navLinks.removeClass('selected');
            activeLink.addClass('selected');
        },
        offset: waypointOffset
    });

    navLinks.on('click', function(event) {
        $.scrollTo(
            $(this).attr('href'),
            {
                duration: 300,
                offset: -waypointOffset+1
            }
        );
    });
});


// usage: log('inside coolFunc', this, arguments);
// paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function(){
  log.history = log.history || [];   // store logs to an array for reference
  log.history.push(arguments);
  arguments.callee = arguments.callee.caller;  
  if(this.console) console.log( Array.prototype.slice.call(arguments) );
};
// make it safe to use console.log always
(function(b){function c(){}for(var d="assert,count,debug,dir,dirxml,error,exception,group,groupCollapsed,groupEnd,info,log,markTimeline,profile,profileEnd,time,timeEnd,trace,warn".split(","),a;a=d.pop();)b[a]=b[a]||c})(window.console=window.console||{});


// place any jQuery/helper plugins in here, instead of separate, slower script files.

