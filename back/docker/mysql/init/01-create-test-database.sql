CREATE DATABASE IF NOT EXISTS forward_test
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON forward_test.* TO 'forward'@'%';
FLUSH PRIVILEGES;
