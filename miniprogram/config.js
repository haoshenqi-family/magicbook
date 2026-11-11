/**
 * 运行时配置：只放「换环境要改」的东西。
 *
 * Why baseUrl 指向 moon-well 而不是 magicbook：词汇数据、复习调度、词汇量测试、
 * 四股台账全部在 moon-well，magicbook 网页层只是代理。
 * 小程序直连后端少一跳，也不依赖网页登录态。
 */
const CONFIG = {
  // 生产后端（Traefik HTTPS 入口）。改指向时同步改小程序后台的 request 合法域名。
  baseUrl: 'https://moon-well.haoshenqi.top',
  // 网页版入口：阅读正文、书库、笔记在那边。小程序只做「掏出手机就能做完」的几件事，
  // 所以这里只做「复制链接」跳转，不做 web-view——OIDC 登录在 web-view 里拿不到浏览器会话。
  siteUrl: 'https://magicbook.haoshenqi.top',
  // 单请求超时（毫秒）。登录/列表都在 1s 级。
  timeout: 15000
};

module.exports = CONFIG;
