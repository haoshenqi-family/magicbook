/**
 * 运行时配置：只放「换环境要改」的东西。
 *
 * Why baseUrl 指向 moon-well 而不是 magicbook：这四个功能的数据与判定全部在
 * moon-well（生词本、复习调度、词汇量测试、四股台账），magicbook 网页层只是代理。
 * 小程序直连后端少一跳，也不依赖网页登录态。
 */
const CONFIG = {
  // 生产后端（Traefik HTTPS 入口）。改指向时同步改小程序后台的 request 合法域名。
  baseUrl: 'https://moon-well.haoshenqi.top',
  // 单请求超时（毫秒）。登录/列表都在 1s 级；批改类长任务不在本小程序范围内。
  timeout: 15000
};

module.exports = CONFIG;
