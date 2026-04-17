-- database.sql

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS careerlens_db;

-- Switch to the new database
USE careerlens_db;

-- Create the history table to store uploaded filenames and their ATS scores
CREATE TABLE IF NOT EXISTS ats_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);