CREATE DATABASE IF NOT EXISTS `knowledge_backend`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `knowledge_backend`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 用户表
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码（bcrypt加密）',
  `nickname` VARCHAR(50) DEFAULT NULL COMMENT '昵称',
  `avatar` VARCHAR(255) DEFAULT 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg' COMMENT '头像URL',
  `gender` ENUM('male', 'female', 'unknown') DEFAULT 'unknown' COMMENT '性别',
  `bio` VARCHAR(500) DEFAULT '这个人很懒, 什么都没留下' COMMENT '个人简介',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`username`),
  UNIQUE KEY `phone_UNIQUE` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 登录令牌表
DROP TABLE IF EXISTS `user_token`;
CREATE TABLE `user_token` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '令牌ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `token` VARCHAR(255) NOT NULL COMMENT 'UUID令牌',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间（通常7天）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_UNIQUE` (`token`),
  KEY `fk_user_token_user_idx` (`user_id`),
  CONSTRAINT `fk_user_token_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户令牌表';

-- 新闻分类表
DROP TABLE IF EXISTS `news_category`;
CREATE TABLE `news_category` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序权重',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻分类表';

-- 新闻表
DROP TABLE IF EXISTS `news`;
CREATE TABLE `news` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '新闻ID',
  `title` VARCHAR(255) NOT NULL COMMENT '标题',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '摘要',
  `content` TEXT NOT NULL COMMENT '正文',
  `image` VARCHAR(255) DEFAULT NULL COMMENT '封面图URL',
  `author` VARCHAR(50) DEFAULT NULL COMMENT '作者',
  `category_id` INT UNSIGNED NOT NULL COMMENT '分类ID',
  `views` INT NOT NULL DEFAULT 0 COMMENT '浏览量',
  `publish_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `fk_news_category_idx` (`category_id`),
  KEY `idx_publish_time` (`publish_time`),
  CONSTRAINT `fk_news_category`
    FOREIGN KEY (`category_id`) REFERENCES `news_category` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻表';

-- 相关新闻关联表（官方物料有这张表；后续接口多按同分类动态查 news）
DROP TABLE IF EXISTS `related_news`;
CREATE TABLE `related_news` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `news_id` INT UNSIGNED NOT NULL COMMENT '当前新闻ID',
  `related_news_id` INT UNSIGNED NOT NULL COMMENT '相关新闻ID',
  PRIMARY KEY (`id`),
  KEY `idx_news_id` (`news_id`),
  KEY `idx_related_news_id` (`related_news_id`),
  CONSTRAINT `fk_related_news_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_related_news_related`
    FOREIGN KEY (`related_news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='相关新闻关联表';

-- 收藏表
DROP TABLE IF EXISTS `favorite`;
CREATE TABLE `favorite` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `news_id` INT UNSIGNED NOT NULL COMMENT '新闻ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_news_unique` (`user_id`, `news_id`),
  KEY `fk_favorite_user_idx` (`user_id`),
  KEY `fk_favorite_news_idx` (`news_id`),
  CONSTRAINT `fk_favorite_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favorite_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏表';

-- 浏览历史表
DROP TABLE IF EXISTS `history`;
CREATE TABLE `history` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '历史ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `news_id` INT UNSIGNED NOT NULL COMMENT '新闻ID',
  `view_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_news_unique` (`user_id`, `news_id`),
  KEY `fk_history_user_idx` (`user_id`),
  KEY `fk_history_news_idx` (`news_id`),
  KEY `idx_view_time` (`view_time`),
  CONSTRAINT `fk_history_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_history_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='浏览历史表';

-- AI 问答记录表
DROP TABLE IF EXISTS `ai_chat`;
CREATE TABLE `ai_chat` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '用户ID',
  `question` TEXT NOT NULL COMMENT '用户问题',
  `answer` TEXT DEFAULT NULL COMMENT 'AI回答',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `fk_ai_chat_user_idx` (`user_id`),
  CONSTRAINT `fk_ai_chat_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI问答记录表';

SET FOREIGN_KEY_CHECKS = 1;

-- 分类种子（方便后面做 /api/news/categories）
INSERT INTO `news_category` (`id`, `name`, `sort_order`) VALUES
  (1, '推荐', 1),
  (2, '热点', 2),
  (3, '科技', 3),
  (4, '财经', 4),
  (5, '体育', 5),
  (6, '娱乐', 6);