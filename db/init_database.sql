-- =====================================================================
-- NCS 기반 지능형 커리어 네비게이터 - DB 스키마 (구조만, 데이터 없음)
-- 실행: mysql -u root -p < db/init_database.sql
-- 주의: 각 테이블 앞에 DROP TABLE IF EXISTS 가 포함되어 있으므로
--       이미 데이터가 있는 DB에서는 실행하지 말고 새 환경에서만 사용하세요.
-- 데이터 적재: data/ 폴더의 스크립트 참고
-- =====================================================================
CREATE DATABASE IF NOT EXISTS career_nav DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE career_nav;

-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: career_nav
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cert_schedules`
--

DROP TABLE IF EXISTS `cert_schedules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cert_schedules` (
  `schedule_id` int NOT NULL AUTO_INCREMENT,
  `cert_id` int NOT NULL,
  `apply_start` date DEFAULT NULL COMMENT '접수 시작일',
  `apply_end` date DEFAULT NULL COMMENT '접수 마감일',
  `exam_date` date DEFAULT NULL COMMENT '시험일',
  `result_date` date DEFAULT NULL COMMENT '합격 발표일',
  `round_name` varchar(30) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `exam_type` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '필기 또는 실기',
  PRIMARY KEY (`schedule_id`),
  KEY `cert_id` (`cert_id`),
  CONSTRAINT `cert_schedules_ibfk_1` FOREIGN KEY (`cert_id`) REFERENCES `certifications` (`cert_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8719 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `certifications`
--

DROP TABLE IF EXISTS `certifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `certifications` (
  `cert_id` int NOT NULL AUTO_INCREMENT,
  `cert_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `issuing_org` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '발급기관',
  `cert_type` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '국가기술, 국가전문, 민간 등',
  `description` text COLLATE utf8mb4_general_ci,
  `competency_units` text COLLATE utf8mb4_general_ci COMMENT '능력단위(직무역량) 목록',
  `ncs_level` int DEFAULT NULL COMMENT 'NCS 수준 (자격증 등급 기반)',
  `career_path` text COLLATE utf8mb4_general_ci COMMENT '진로 및 전망',
  `pass_rate` float DEFAULT NULL COMMENT '합격률(%)',
  PRIMARY KEY (`cert_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1334 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `job_certifications`
--

DROP TABLE IF EXISTS `job_certifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_certifications` (
  `job_id` int NOT NULL,
  `cert_id` int NOT NULL,
  PRIMARY KEY (`job_id`,`cert_id`),
  KEY `cert_id` (`cert_id`),
  CONSTRAINT `job_certifications_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`),
  CONSTRAINT `job_certifications_ibfk_2` FOREIGN KEY (`cert_id`) REFERENCES `certifications` (`cert_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `job_id` int NOT NULL AUTO_INCREMENT,
  `ncs_id` int NOT NULL,
  `job_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `required_skills` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`job_id`),
  KEY `ncs_id` (`ncs_id`),
  CONSTRAINT `jobs_ibfk_1` FOREIGN KEY (`ncs_id`) REFERENCES `ncs_categories` (`ncs_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ncs_categories`
--

DROP TABLE IF EXISTS `ncs_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ncs_categories` (
  `ncs_id` int NOT NULL AUTO_INCREMENT,
  `lclas_cd` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `lclas_nm` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `mclas_cd` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `mclas_nm` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sclas_cd` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sclas_nm` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dclas_cd` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dclas_nm` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `duty_def` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`ncs_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3304 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recommendations`
--

DROP TABLE IF EXISTS `recommendations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recommendations` (
  `rec_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `job_id` int NOT NULL,
  `cert_id` int NOT NULL,
  `match_score` float DEFAULT NULL COMMENT '매칭 점수 (0~1)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rec_id`),
  KEY `user_id` (`user_id`),
  KEY `job_id` (`job_id`),
  KEY `cert_id` (`cert_id`),
  CONSTRAINT `recommendations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `recommendations_ibfk_2` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`),
  CONSTRAINT `recommendations_ibfk_3` FOREIGN KEY (`cert_id`) REFERENCES `certifications` (`cert_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_bookmarks`
--

DROP TABLE IF EXISTS `user_bookmarks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_bookmarks` (
  `bookmark_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `cert_id` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`bookmark_id`),
  UNIQUE KEY `unique_bookmark` (`user_id`,`cert_id`),
  KEY `cert_id` (`cert_id`),
  CONSTRAINT `user_bookmarks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `user_bookmarks_ibfk_2` FOREIGN KEY (`cert_id`) REFERENCES `certifications` (`cert_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `major` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `interest_field` text COLLATE utf8mb4_general_ci,
  `owned_certs` text COLLATE utf8mb4_general_ci,
  `experience` text COLLATE utf8mb4_general_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `education` varchar(50) COLLATE utf8mb4_general_ci DEFAULT '4년제대졸이상',
  `career_years` int DEFAULT '0',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-28 15:32:02
