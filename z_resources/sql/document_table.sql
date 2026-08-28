-- ============================================================
-- 文档模块建表脚本（MySQL 8）
-- 依赖：先执行 projectTable.sql（需已有 user 表）
-- ============================================================

USE `knowledge_backend`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 文档分类表
DROP TABLE IF EXISTS `document`;
DROP TABLE IF EXISTS `document_category`;

CREATE TABLE `document_category` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序权重',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_document_category_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档分类表';

-- 文档表
CREATE TABLE `document` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文档ID',
  `user_id` INT UNSIGNED NOT NULL COMMENT '上传用户ID',
  `category_id` INT UNSIGNED NOT NULL COMMENT '分类ID',
  `title` VARCHAR(255) NOT NULL COMMENT '文档标题',
  `description` VARCHAR(500) NOT NULL COMMENT '文档描述',
  `file_name` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_path` VARCHAR(500) NOT NULL COMMENT '文件存储路径',
  `file_size` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小（字节）',
  `file_type` VARCHAR(100) DEFAULT NULL COMMENT 'MIME类型，如 application/pdf',
  `file_ext` VARCHAR(20) DEFAULT NULL COMMENT '文件扩展名，如 pdf、txt、md',
  `status` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '处理状态：0待解析 1解析中 2已完成 3失败',
  `preview_text` MEDIUMTEXT DEFAULT NULL COMMENT '解析后的文本预览',
  `parse_error` VARCHAR(500) DEFAULT NULL COMMENT '解析失败原因',
  `chunk_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '分片数量（RAG用）',
  `upload_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_document_user_id` (`user_id`),
  KEY `idx_document_category_id` (`category_id`),
  KEY `idx_document_status` (`status`),
  KEY `idx_document_upload_time` (`upload_time`),
  CONSTRAINT `fk_document_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_document_category`
    FOREIGN KEY (`category_id`) REFERENCES `document_category` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';

SET FOREIGN_KEY_CHECKS = 1;

-- 分类初始数据（对应前端文档分类）
INSERT INTO `document_category` (`id`, `name`, `sort_order`) VALUES
  (1, '技术文档', 1),
  (2, '产品手册', 2),
  (3, '政策法规', 3),
  (4, '培训资料', 4);
