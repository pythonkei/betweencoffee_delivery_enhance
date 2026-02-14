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


// Payment Reminder Popup 功能 - 全局版本
class PaymentReminder {
    constructor() {
        this.popup = document.getElementById('payment-reminder-popup');
        this.orderId = null;
        this.countdownInterval = null;
        this.autoHideTimeout = null;
        this.isVisible = false;
        this.init();
    }

    init() {
        // 确保popup存在
        if (!this.popup) {
            console.warn('Payment reminder popup element not found');
            return;
        }
        
        // 绑定事件
        const payNowBtn = document.getElementById('reminder-pay-now');
        const dismissBtn = document.getElementById('reminder-dismiss');
        
        if (payNowBtn) {
            payNowBtn.addEventListener('click', () => this.handlePayNow());
        }
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this.hide());
        }
        
        // 检查是否有需要显示的支付提醒
        this.checkPendingReminders();
        
        // 设置全局事件监听
        this.setupGlobalListeners();
    }

    setupGlobalListeners() {
        // 监听来自其他页面的支付提醒事件
        document.addEventListener('paymentReminderShow', (event) => {
            if (event.detail && event.detail.order) {
                this.showReminder(event.detail.order);
            }
        });
        
        // 监听支付成功事件
        document.addEventListener('paymentSuccess', () => {
            this.hide();
        });
    }

    checkPendingReminders() {
        // 从localStorage检查
        const pendingOrder = localStorage.getItem('pending_payment_order');
        if (pendingOrder) {
            try {
                const orderData = JSON.parse(pendingOrder);
                // 检查订单是否仍然有效
                if (this.isOrderValid(orderData)) {
                    this.showReminder(orderData);
                } else {
                    localStorage.removeItem('pending_payment_order');
                }
            } catch (e) {
                localStorage.removeItem('pending_payment_order');
            }
        }
        
        // 从API获取待支付订单（如果用户已登录）
        this.fetchPendingOrders();
    }

    isOrderValid(orderData) {
        // 检查订单是否仍然有效（未超时）
        if (!orderData.payment_timeout) return false;
        
        const timeout = new Date(orderData.payment_timeout);
        const now = new Date();
        return timeout > now;
    }

    fetchPendingOrders() {
        // 检查用户是否登录（简单检查是否有用户相关元素）
        const userElements = document.querySelector('[data-user], .user-info, #user-menu');
        if (!userElements) return;
        
        fetch('/eshop/api/pending-orders/')
            .then(response => {
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(data => {
                if (data.orders && data.orders.length > 0) {
                    const urgentOrder = data.orders.find(order => 
                        order.minutes_remaining <= 5 && order.minutes_remaining > 0
                    );
                    if (urgentOrder) {
                        this.showReminder(urgentOrder);
                    }
                }
            })
            .catch(error => console.debug('获取待支付订单失败或用户未登录:', error));
    }

    showReminder(orderData) {
        if (this.isVisible) return; // 防止重复显示
        
        this.orderId = orderData.id;
        this.isVisible = true;
        
        // 更新弹出窗口内容
        const orderName = document.getElementById('reminder-order-name');
        const message = document.getElementById('reminder-message');
        const timeLeft = document.getElementById('reminder-time-left');
        
        if (orderName) orderName.textContent = `订单 #${orderData.id}`;
        if (message) {
            message.textContent = 
                `您的订单还有${orderData.minutes_remaining}分钟即将超时，请及时支付`;
        }
        
        // 显示弹出窗口
        this.popup.style.display = 'block';
        setTimeout(() => {
            this.popup.classList.add('show');
        }, 100);

        // 开始倒计时
        this.startCountdown(orderData.minutes_remaining * 60);
        
        // 10秒后自动隐藏（但保持后台检查）
        this.autoHideTimeout = setTimeout(() => {
            this.hide();
        }, 10000);
        
        // 保存到localStorage
        localStorage.setItem('pending_payment_order', JSON.stringify(orderData));
        
        // 触发全局事件
        document.dispatchEvent(new CustomEvent('paymentReminderShown', {
            detail: { order: orderData }
        }));
    }

    startCountdown(totalSeconds) {
        const timeElement = document.getElementById('reminder-time-left');
        if (!timeElement) return;
        
        this.countdownInterval = setInterval(() => {
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            
            timeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // 添加闪烁动画
            timeElement.classList.add('countdown-animation');
            setTimeout(() => {
                timeElement.classList.remove('countdown-animation');
            }, 500);
            
            if (totalSeconds <= 0) {
                this.hide();
                return;
            }
            
            totalSeconds--;
        }, 1000);
    }

    handlePayNow() {
        if (this.orderId) {
            // 跳转到支付页面
            window.location.href = `/eshop/continue_payment/${this.orderId}/`;
        } else {
            // 跳转到订单历史
            window.location.href = '/accounts/order_history/';
        }
        this.hide();
    }

    hide() {
        this.isVisible = false;
        
        // 清除定时器
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }
        
        // 隐藏弹出窗口
        if (this.popup) {
            this.popup.classList.remove('show');
            this.popup.classList.add('hide');
            
            setTimeout(() => {
                this.popup.style.display = 'none';
                this.popup.classList.remove('hide');
            }, 500);
        }
        
        // 从localStorage移除
        localStorage.removeItem('pending_payment_order');
    }

    // 静态方法：从任何地方触发支付提醒
    static showGlobalReminder(orderData) {
        document.dispatchEvent(new CustomEvent('paymentReminderShow', {
            detail: { order: orderData }
        }));
    }
}

// 页面加载后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.paymentReminder = new PaymentReminder();
    
    // 全局检查支付提醒
    function checkAndShowPaymentReminders() {
        if (window.paymentReminder && !window.paymentReminder.isVisible) {
            window.paymentReminder.checkPendingReminders();
        }
    }

    // 页面加载后检查
    setTimeout(checkAndShowPaymentReminders, 3000);
    
    // 每30秒检查一次
    setInterval(checkAndShowPaymentReminders, 30000);
});

// 手动触发支付提醒的测试函数（开发时使用）
window.testPaymentReminder = function(orderId = 123, minutesLeft = 5) {
    if (window.paymentReminder) {
        window.paymentReminder.showReminder({
            id: orderId,
            minutes_remaining: minutesLeft,
            payment_timeout: new Date(Date.now() + minutesLeft * 60000).toISOString()
        });
    }
};

// 从任何地方触发支付提醒
window.showPaymentReminder = function(orderData) {
    PaymentReminder.showGlobalReminder(orderData);
};


// 页面加载后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.paymentReminder = new PaymentReminder();
    
    // 手动触发支付提醒的测试函数（开发时使用）
    window.testPaymentReminder = function(orderId = 123, minutesLeft = 5) {
        window.paymentReminder.showReminder({
            id: orderId,
            minutes_remaining: minutesLeft
        });
    };
});