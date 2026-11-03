/**
 * 小程序入口。冷启动落在登录页（app.json pages 首项），
 * 已登录由登录页自己 switchTab 到复习（tabBar 第一项）——入口逻辑集中在一处，避免两处各自判断。
 */
App({
  globalData: {
    appName: 'MagicBook 工具'
  },

  onLaunch() {
    // 预留：版本检查/埋点等启动期动作。当前无必须动作，保持空实现而不是假装有。
  }
});
