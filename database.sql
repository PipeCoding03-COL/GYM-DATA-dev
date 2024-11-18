-- Schema para la base de datos
CREATE DATABASE IF NOT EXISTS login_flask;
USE login_flask;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    survey_completed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS exercise_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    exercise_type VARCHAR(50) NOT NULL,
    frequency INT NOT NULL,
    experience_level VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS muscle_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    muscle_group VARCHAR(50) NOT NULL,
    priority INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Datos predefinidos para las opciones de la encuesta
CREATE TABLE IF NOT EXISTS exercise_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

INSERT INTO exercise_types (name, description) VALUES
    ('Cardio', 'Ejercicios aeróbicos como correr, nadar, ciclismo'),
    ('Pesas', 'Entrenamiento con pesas y resistencia'),
    ('Calistenia', 'Ejercicios con peso corporal'),
    ('Yoga', 'Ejercicios de flexibilidad y equilibrio'),
    ('HIIT', 'Entrenamiento de alta intensidad por intervalos');

CREATE TABLE IF NOT EXISTS muscle_group_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

INSERT INTO muscle_group_options (name) VALUES
    ('Piernas'),
    ('Pecho'),
    ('Espalda'),
    ('Hombros'),
    ('Brazos'),
    ('Core'),
    ('Glúteos');

CREATE TABLE weight_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    date_recorded DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    muscle_group VARCHAR(50) NOT NULL,
    measurement DECIMAL(5,2) NOT NULL,
    date_recorded DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE measurement_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notification_date DATE NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    exercise_type VARCHAR(50) NOT NULL,
    sets INT NOT NULL,
    reps INT NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    date_recorded DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
