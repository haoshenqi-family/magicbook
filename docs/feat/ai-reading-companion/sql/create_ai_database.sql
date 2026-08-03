-- AI Reading Companion 独立数据库建库脚本
-- 执行环境：MySQL 实例 192.168.31.9:3306（用户名 HSQ，需具备 CREATE 权限）
-- 用法：mysql -h 192.168.31.9 -u HSQ -p < create_ai_database.sql
-- 说明：ai_* 表由应用启动时通过 SQLAlchemy create_all 自动创建，本脚本仅建库并授权。

CREATE DATABASE IF NOT EXISTS ai_companion
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 若 HSQ 用户需显式授权（按实际账号调整）
GRANT ALL PRIVILEGES ON ai_companion.* TO 'HSQ'@'%';
FLUSH PRIVILEGES;
