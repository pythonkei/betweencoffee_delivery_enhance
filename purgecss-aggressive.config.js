    './templates/**/*.html',
    './eshop/templates/**/*.html',
    './cart/templates/**/*.html',
    './restaurant/templates/**/*.html',
    './socialuser/templates/**/*.html',
  ],
  
  css: ['./static/css/style.css'],
  
  output: './static/css/dist-aggressive/',
  
  // 更激進的配置
  defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
  
  safelist: {
    standard: [
      // 基本類名
      'active', 'disabled', 'show', 'hide', 'fade',
      'btn', 'modal', 'alert', 'badge', 'card',
      'nav-', 'page-', 'user-', 'menu-', 'order-',
      'col-', 'row', 'container', 'form-',
      // Bootstrap網格系統
      /^col-/, /^row/, /^container/, /^d-/, /^m[tyblr]?-/, /^p[tyblr]?-/, /^text-/,
      // 狀態類
      /^is-/, /^has-/, /^js-/, /^data-/,
    ],
    deep: [],
    greedy: [],
    keyframes: [],
    variables: []
  },
  
  // 啟用壓縮
  compressed: true,
  
  // 詳細輸出
  verbose: true,
  
  // 不保留字體定義
  fontFace: false,
  
  // 不保留關鍵幀
  keyframes: false,
  
  // 不保留變量
  variables: false,
