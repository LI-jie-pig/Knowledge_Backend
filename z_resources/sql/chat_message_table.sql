-- ============================================================
-- AI 会话记忆表（MySQL 8）
-- 用途：按 session_id 持久化多轮对话消息，替代 Redis 缓存
-- ============================================================

USE `knowledge_backend`;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `chat_message` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `session_id` VARCHAR(64) NOT NULL COMMENT '会话ID',
  `role` VARCHAR(20) NOT NULL COMMENT '角色：user/assistant',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_message_session_id` (`session_id`),
  KEY `idx_chat_message_session_created` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI会话消息表';
