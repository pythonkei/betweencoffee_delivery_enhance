 AOS.init({
 	duration: 800,
 	easing: 'slide'
 });

(function($) {

	"use strict";

	$(window).stellar({
    responsive: true,
    parallaxBackgrounds: true,
    parallaxElements: true,
    horizontalScrolling: false,
    hideDistantElements: false,
    scrollProperty: 'scroll',
    horizontalOffset: 0,
	  verticalOffset: 0
  });

  // Scrollax
  $.Scrollax();


	var fullHeight = function() {

		$('.js-fullheight').css('height', $(window).height());
		$(window).resize(function(){
			$('.js-fullheight').css('height', $(window).height());
		});

	};
	fullHeight();

	// loader
	var loader = function() {
		setTimeout(function() { 
			if($('#ftco-loader').length > 0) {
				$('#ftco-loader').removeClass('show');
			}
		}, 1);
	};
	loader();

	// Scrollax
   $.Scrollax();


// owl-carousel slider control & transitions > config file: animate.css
	var carousel = function() {
		$('.home-slider').owlCarousel({
	    loop:true,
	    autoplay: true,
		autoplayTimeout:8000, // time per slide
	    margin:0,
	    animateOut: 'fadeOutUpBig ',
	    animateIn: 'fadeInUp',
	    nav:false,
	    autoplayHoverPause: false,
	    items: 1,
	    navText : ["<span class='ion-md-arrow-back'></span>","<span class='ion-chevron-right'></span>"],
	    responsive:{
	      0:{
	        items:1,
	        nav:false
	      },
	      600:{
	        items:1,
	        nav:false
	      },
	      1000:{
	        items:1,
	        nav:false
	      }
	    }
		});
		$('.carousel-work').owlCarousel({
			autoplay: true,
			center: true,
			loop: true,
			items:1,
			margin: 30,
			stagePadding:0,
			nav: true,
			navText: ['<span class="ion-ios-arrow-back">', '<span class="ion-ios-arrow-forward">'],
			responsive:{
				0:{
					items: 1,
					stagePadding: 0
				},
				600:{
					items: 2,
					stagePadding: 50
				},
				1000:{
					items: 3,
					stagePadding: 100
				}
			}
		});

	};
	carousel();

	$('nav .dropdown').hover(function(){
		var $this = $(this);
		// 	 timer;
		// clearTimeout(timer);
		$this.addClass('show');
		$this.find('> a').attr('aria-expanded', true);
		// $this.find('.dropdown-menu').addClass('animated-fast fadeInUp show');
		$this.find('.dropdown-menu').addClass('show');
	}, function(){
		var $this = $(this);
			// timer;
		// timer = setTimeout(function(){
			$this.removeClass('show');
			$this.find('> a').attr('aria-expanded', false);
			// $this.find('.dropdown-menu').removeClass('animated-fast fadeInUp show');
			$this.find('.dropdown-menu').removeClass('show');
		// }, 100);
	});


	$('#dropdown04').on('show.bs.dropdown', function () {
	  console.log('show');
	});

	// scroll
	var scrollWindow = function() {
		$(window).scroll(function(){
			var $w = $(this),
					st = $w.scrollTop(),
					navbar = $('.ftco_navbar'),
					sd = $('.js-scroll-wrap');

			if (st > 150) {
				if ( !navbar.hasClass('scrolled') ) {
					navbar.addClass('scrolled');	
				}
			} 
			if (st < 150) {
				if ( navbar.hasClass('scrolled') ) {
					navbar.removeClass('scrolled sleep');
				}
			} 
			if ( st > 350 ) {
				if ( !navbar.hasClass('awake') ) {
					navbar.addClass('awake');	
				}
				
				if(sd.length > 0) {
					sd.addClass('sleep');
				}
			}
			if ( st < 350 ) {
				if ( navbar.hasClass('awake') ) {
					navbar.removeClass('awake');
					navbar.addClass('sleep');
				}
				if(sd.length > 0) {
					sd.removeClass('sleep');
				}
			}
		});
	};
	scrollWindow();

	
	var counter = function() {
		
		$('#section-counter').waypoint( function( direction ) {

			if( direction === 'down' && !$(this.element).hasClass('ftco-animated') ) {

				var comma_separator_number_step = $.animateNumber.numberStepFactories.separator(',')
				$('.number').each(function(){
					var $this = $(this),
						num = $this.data('number');
						console.log(num);
					$this.animateNumber(
					  {
					    number: num,
					    numberStep: comma_separator_number_step
					  }, 7000
					);
				});
				
			}

		} , { offset: '95%' } );

	}
	counter();

	var contentWayPoint = function() {
		var i = 0;
		$('.ftco-animate').waypoint( function( direction ) {

			if( direction === 'down' && !$(this.element).hasClass('ftco-animated') ) {
				
				i++;

				$(this.element).addClass('item-animate');
				setTimeout(function(){

					$('body .ftco-animate.item-animate').each(function(k){
						var el = $(this);
						setTimeout( function () {
							var effect = el.data('animate-effect');
							if ( effect === 'fadeIn') {
								el.addClass('fadeIn ftco-animated');
							} else if ( effect === 'fadeInLeft') {
								el.addClass('fadeInLeft ftco-animated');
							} else if ( effect === 'fadeInRight') {
								el.addClass('fadeInRight ftco-animated');
							} else {
								el.addClass('fadeInUp ftco-animated');
							}
							el.removeClass('item-animate');
						},  k * 50, 'easeInOutExpo' );
					});
					
				}, 100);
				
			}

		} , { offset: '95%' } );
	};
	contentWayPoint();


	// navigation
	var OnePageNav = function() {
		$(".smoothscroll[href^='#'], #ftco-nav ul li a[href^='#']").on('click', function(e) {
		 	e.preventDefault();

		 	var hash = this.hash,
		 			navToggler = $('.navbar-toggler');
		 	$('html, body').animate({
		    scrollTop: $(hash).offset().top
		  }, 700, 'easeInOutExpo', function(){
		    window.location.hash = hash;
		  });


		  if ( navToggler.is(':visible') ) {
		  	navToggler.click();
		  }
		});
		$('body').on('activate.bs.scrollspy', function () {
		  console.log('nice');
		})
	};
	OnePageNav();


	// magnific popup
	$('.image-popup').magnificPopup({
    type: 'image',
    closeOnContentClick: true,
    closeBtnInside: true,
    fixedContentPos: true,
    mainClass: 'mfp-no-margins mfp-with-zoom', // class to remove default margin from left and right side
     gallery: {
      enabled: true,
      navigateByImgClick: true,
      preload: [0,1] // Will preload 0 - before current, and 1 after the current image
    },
    image: {
      verticalFit: true
    },
    zoom: {
      enabled: true,
      duration: 300 // don't foget to change the duration also in CSS
    }
  });

  $('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
    disableOn: 700,
    type: 'iframe',
    mainClass: 'mfp-fade',
    removalDelay: 160,
    preloader: false,

    fixedContentPos: false
  });


	$('.appointment_date').datepicker({
		'format': 'm/d/yyyy',
		'autoclose': true
	});

    // Get current time
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';

    // Convert to 12-hour format
    hours = hours % 12;
    hours = hours ? hours : 12; // Handle midnight (0 hours)

    // Format time as h:mm AM/PM
    const currentTime = `${hours}:${minutes < 10 ? '0' + minutes : minutes} ${ampm}`;
	
    // Initialize timepicker with current time as default
    $('#time').timepicker({
        timeFormat: 'h:mm p',  // Display format (e.g., 2:30 PM)
        interval: 5,           // 5-minute intervals
        minTime: '7:00am',      // Minimum time
        maxTime: '8:00pm',      // Maximum time
        defaultTime: currentTime, // Set current time as default
        dropdown: true,
        showDuration: true      // Show duration between times
	});

})(jQuery);



//アコーディオンをクリックした時の動作
$('.title').on('click', function() {
	$('.box-1').slideUp(500);
    
	var findElm = $(this).next(".box-1");
    
	if($(this).hasClass('close')){
		$(this).removeClass('close');   
	}else{//それ以外は
		$('.close').removeClass('close');
		$(this).addClass('close');
		$(findElm).slideDown(500);
	}
});


/* ハンバーガーメニュー動作 */
$(function () {
	// ハンバーガーメニューのクリックイベント
	  $('.openbtn').on('click', function () {
		  if ($('#header').hasClass('open')) {
			  $('#header').removeClass('open');
		  } else {
			  $('#header').addClass('open');
		  }
	  });
  
	  // #maskのエリアをクリックした時にメニューを閉じる
	  $('#mask').on('click', function () {
		  $('#header').removeClass('open');
		  $('#navi').removeClass('panelactive');
		  $('.openbtn').removeClass('active');
	  });
  
	  // リンクをクリックした時にメニューを閉じる
	  $('#navi a').on('click', function () {
		  $('#header').removeClass('open');
	  });
	  
	  $('.openbtn').click(function() {
		  $(this).toggleClass('active');
		  $("#navi").toggleClass('panelactive');
	  });
  
	  $('.menu li a').click(function() {
		  $('.openbtn').removeClass('active');
		  $("#navi").removeClass('panelactive');
	  });
  
	  $('.corporate').click(function() {
		  $('.openbtn').removeClass('active');
		  $("#navi").removeClass('panelactive');
	  });
  
	  $('.entry li a').click(function() {
		  $('.openbtn').removeClass('active');
		  $("#navi").removeClass('panelactive');
	  });
  });
  
  window.addEventListener('unload', function () {
	  $('.openbtn').removeClass('active');
  });

  
/* Infinite Scrolling Text */
const scrollers = document.querySelectorAll('.scroller');

if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches)
{
addAnimation();
}

function addAnimation() {
scrollers.forEach(scroller => {
	scroller.setAttribute('data-animated', true);
	
	const scrollerInner = scroller.querySelector('.scroller__inner');
	const scrollerContent = Array.from(scrollerInner.children);
	
	scrollerContent.forEach(item => {
	const duplicatedItem = item.cloneNode(true);
	duplicatedItem.setAttribute("aria-hidden", true);
	scrollerInner.appendChild(duplicatedItem);
	}) 
});
}


// Order detail - Collapse to Accordions by default hidden //
(function ($) {
	"use strict";
	$.fn.responsiveTable = function() { 
  
	  var toggleColumns = function($table) {
		var selectedControls = [];
		$table.find(".Accordion, .Tab").each( function() {
		  selectedControls.push( $(this).attr("aria-selected") );
		});
		var cellCount = 0, colCount = 0;
		var setNum = $table.find(".Rtable-cell").length / Math.max( $table.find(".Tab").length, $table.find(".Accordion").length );
		$table.find(".Rtable-cell").each( function() {
		  $(this).addClass("hiddenSmall");
		  if( selectedControls[colCount] === "true" ) $(this).removeClass("hiddenSmall");
		  cellCount++;
		  if( cellCount % setNum === 0 ) colCount++; 
		});
	  };
	  $(this).each(function(){ toggleColumns($(this)); });
  
	  $(this).find(".Tab").click( function() {
		$(this).attr("aria-selected","true").siblings().attr("aria-selected","false");
		toggleColumns( $(this).parents(".Rtable") );
	  });
  
	  $(this).find(".Accordion").click( function() {
		$(this).attr("aria-selected", $(this).attr("aria-selected") !== "true" );
		toggleColumns( $(this).parents(".Rtable") );
	  });
  
	};
  }(jQuery));
  
  
  $(".js-RtableTabs, .js-RtableAccordions").responsiveTable();




/*Time global jQuery*/

(function ($) {

    /*
     * 現在時刻の表示
     */
    function updateClock() {
        // 現在の日時を取得
        const now = new Date();
  
        // 時、分、秒を取得
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();
  
        // 時、分、秒が1桁の場合は0を追加
        const displayHours = hours.toString().padStart(2, "0");
        const displayMinutes = minutes.toString().padStart(2, "0");
        const displaySeconds = seconds.toString().padStart(2, "0");
  
        // 時計の要素を取得
        const clockElement = document.getElementById("clock");
  
        // 時計の要素に時刻を表示
        clockElement.textContent = `${displayHours}:${displayMinutes}:${displaySeconds}`;
  
        // 1秒後に再度更新
        setTimeout(updateClock, 1000);
    }
  
    // 時計を開始
    updateClock();


    // スクロールイベント
    $(window).on('scroll', function(){

        // ヘッダー表示
        if( $(this).scrollTop() > 100 ) {
            $('.header__logo').addClass('active');
        } else {
            $('.header__logo').removeClass('active');
        }
    });


}) ( jQuery );