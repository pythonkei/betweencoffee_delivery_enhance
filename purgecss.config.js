// purgecss.config.js
module.exports = {
  // 指定所有 HTML 模板文件（使用 glob 模式匹配）
  content: [
    './templates/**/*.html',              // 根 templates 目录
    './eshop/templates/**/*.html',         // eshop 应用的模板
    './cart/templates/**/*.html',           // cart 应用的模板
    // 如果有更多模板目录，继续添加
  ],

  // 指定要清理的 CSS 文件
  css: ['./static/css/style.css'],

  // 输出目录（建议先输出到新文件夹，检查后再替换原文件）
  output: './static/css/dist/',

  // 关键：配置白名单，防止误删动态类名
  safelist: {
    standard: [
      // 完全匹配的类名（例如始终保留 'btn' 和 'modal'）
      'btn',
      'modal',
      // 可以加上你可能从 Django 变量中拼接的类名前缀
      /^nav-/,        // 保留所有以 'nav-' 开头的类名，如 nav-item, nav-link
      /^page-/,       // 保留所有以 'page-' 开头的类名
      /^user-/,       // 保留所有以 'user-' 开头的类名
      // 如果你使用了任何 JavaScript 插件动态添加的类，也要加进来
      'active',
      'disabled',
      'show',
      'fade',
    ],
    // 也可以根据正则表达式保留（上面已经用了正则）
  },
}