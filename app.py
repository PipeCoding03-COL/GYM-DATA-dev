from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Configuración MySQL
app.config['MYSQL_HOST'] = 'bsysaxfnwnmjiwl9jwbv-mysql.services.clever-cloud.com'
app.config['MYSQL_USER'] = 'u1kgz8px7ujltpfx'
app.config['MYSQL_PASSWORD'] = 'gpMat0GtmQd2G15i9Jho'
app.config['MYSQL_DB'] = 'bsysaxfnwnmjiwl9jwbv'

# Inicializar MySQL
mysql = MySQL(app)

# Configuración de la aplicación
app.secret_key = 'tu_clave_secreta_aqui'

# Rutas de la aplicación
# Ruta-Login
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form['username']
        password = request.form['password']
        
        # Verificar si el usuario existe
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            # Crear sesión
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            survey_completed = cursor.execute('SELECT survey_completed FROM users WHERE id = %s', (session['id'],))
            if survey_completed:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('survey'))
        else:
            msg = 'Usuario o contraseña incorrectos!'
    
    return render_template('login.html', msg=msg)

# Ruta-Survey
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        # Limpiar preferencias anteriores del usuario
        cursor.execute('DELETE FROM exercise_preferences WHERE user_id = %s', (session['id'],))
        cursor.execute('DELETE FROM muscle_groups WHERE user_id = %s', (session['id'],))
        
        # Guardar nuevas preferencias de ejercicios
        exercise_types = request.form.getlist('exercise_types')
        for exercise in exercise_types:
            frequency = request.form.get(f'frequency_{exercise}')
            experience = request.form.get(f'experience_{exercise}')
            cursor.execute('''
                INSERT INTO exercise_preferences (user_id, exercise_type, frequency, experience_level)
                VALUES (%s, %s, %s, %s)
            ''', (session['id'], exercise, frequency, experience))
        
        # Guardar grupos musculares priorizados
        muscle_groups = request.form.getlist('muscle_groups')
        for i, muscle in enumerate(muscle_groups):
            cursor.execute('''
                INSERT INTO muscle_groups (user_id, muscle_group, priority)
                VALUES (%s, %s, %s)
            ''', (session['id'], muscle, i+1))
        
        # Marcar encuesta como completada
        cursor.execute('UPDATE users SET survey_completed = TRUE WHERE id = %s', (session['id'],))
        mysql.connection.commit()
        
        return redirect(url_for('dashboard'))
    
    # Obtener opciones para la encuesta
    cursor.execute('SELECT * FROM exercise_types')
    exercise_types = cursor.fetchall()
    
    cursor.execute('SELECT * FROM muscle_group_options')
    muscle_groups = cursor.fetchall()
    
    # Obtener respuestas anteriores si existen
    cursor.execute('SELECT * FROM exercise_preferences WHERE user_id = %s', (session['id'],))
    user_preferences = cursor.fetchall()
    
    cursor.execute('SELECT * FROM muscle_groups WHERE user_id = %s ORDER BY priority', (session['id'],))
    user_muscle_groups = cursor.fetchall()
    
    return render_template('survey.html', 
                         exercise_types=exercise_types,
                         muscle_groups=muscle_groups,
                         user_preferences=user_preferences,
                         user_muscle_groups=user_muscle_groups)

# Ruta-Dashboard
@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT survey_completed FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    
    if not user['survey_completed']:
        return redirect(url_for('survey'))
    
    # Obtener preferencias del usuario
    cursor.execute('''
        SELECT ep.*, et.description 
        FROM exercise_preferences ep 
        JOIN exercise_types et ON ep.exercise_type = et.name 
        WHERE user_id = %s
    ''', (session['id'],))
    preferences = cursor.fetchall()
    
    cursor.execute('SELECT * FROM muscle_groups WHERE user_id = %s ORDER BY priority', (session['id'],))
    muscle_groups = cursor.fetchall()
    
    return render_template('dashboard.html',
                         username=session['username'],
                         preferences=preferences,
                         muscle_groups=muscle_groups)

# Ruta-Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Verificar si el usuario ya existe
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            msg = 'La cuenta ya existe!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Dirección de correo inválida!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'El usuario debe contener solo caracteres y números!'
        else:
            # Hash de la contraseña
            hashed_password = generate_password_hash(password)
            # Insertar nuevo usuario
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s)', (username, hashed_password, email, 0))
            mysql.connection.commit()
            msg = 'Te has registrado exitosamente!'
            return redirect(url_for('login'))
            
    return render_template('register.html', msg=msg)

# Ruta-DeleteWorkout
@app.route('/delete_workout/<int:workout_id>')
def delete_workout(workout_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM workouts WHERE id = %s AND user_id = %s', (workout_id, session['id']))
    mysql.connection.commit()
    
    return redirect(url_for('track'))


# Ruta-Track
@app.route('/track', methods=['GET', 'POST'])
def track():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    
    # Get exercise types for dropdown
    cursor.execute('SELECT * FROM exercise_types')
    exercise_types = cursor.fetchall()
    
    # Get time period filter from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if request.method == 'POST':
        if 'workout_submit' in request.form:
            # Handle workout submission
            exercise_type = request.form.get('exercise_type')
            sets = request.form.get('sets')
            reps = request.form.get('reps')
            weight = request.form.get('exercise_weight')
            workout_date = request.form.get('workout_date')
            
            cursor.execute('''
                INSERT INTO workouts 
                (user_id, exercise_type, sets, reps, weight, date_recorded)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (session['id'], exercise_type, sets, reps, weight, workout_date))
            mysql.connection.commit()
            msg = 'Entrenamiento registrado exitosamente!'
        else:
            # Handle weight tracking
            weight = request.form.get('weight')
            weight_date = request.form.get('weight_date')
            
            cursor.execute('''
                INSERT INTO weight_tracking (user_id, weight, date_recorded)
                VALUES (%s, %s, %s)
            ''', (session['id'], weight, weight_date))
            
            # Handle measurements tracking
            muscle_groups = ['arms', 'chest', 'legs', 'waist', 'shoulders']
            measurement_date = request.form.get('measurement_date')
            
            for muscle in muscle_groups:
                measurement = request.form.get(muscle)
                if measurement:
                    cursor.execute('''
                        INSERT INTO measurements (user_id, muscle_group, measurement, date_recorded)
                        VALUES (%s, %s, %s, %s)
                    ''', (session['id'], muscle, measurement, measurement_date))
            
            mysql.connection.commit()
            msg = 'Medidas registradas exitosamente!'
    
    # Get workout history with date filtering
    if start_date and end_date:
        cursor.execute('''
            SELECT w.*, et.description 
            FROM workouts w 
            JOIN exercise_types et ON w.exercise_type = et.name 
            WHERE w.user_id = %s 
            AND w.date_recorded BETWEEN %s AND %s
            ORDER BY w.date_recorded DESC
        ''', (session['id'], start_date, end_date))
    else:
        cursor.execute('''
            SELECT w.*, et.description 
            FROM workouts w 
            JOIN exercise_types et ON w.exercise_type = et.name 
            WHERE w.user_id = %s 
            ORDER BY w.date_recorded DESC
        ''', (session['id'],))
    
    workout_history = cursor.fetchall()
    
    # Get weight history with date filtering
    if start_date and end_date:
        cursor.execute('''
            SELECT * FROM weight_tracking 
            WHERE user_id = %s 
            AND date_recorded BETWEEN %s AND %s 
            ORDER BY date_recorded
        ''', (session['id'], start_date, end_date))
    else:
        cursor.execute('''
            SELECT * FROM weight_tracking 
            WHERE user_id = %s 
            ORDER BY date_recorded
        ''', (session['id'],))
    
    weight_history = cursor.fetchall()
    
    # Get measurements history with date filtering
    if start_date and end_date:
        cursor.execute('''
            SELECT * FROM measurements 
            WHERE user_id = %s 
            AND date_recorded BETWEEN %s AND %s 
            ORDER BY date_recorded
        ''', (session['id'], start_date, end_date))
    else:
        cursor.execute('''
            SELECT * FROM measurements 
            WHERE user_id = %s 
            ORDER BY date_recorded
        ''', (session['id'],))
    
    measurements_history = cursor.fetchall()
    
    # Generate graphs
    weight_graph = generate_weight_graph(weight_history)
    measurements_graph = generate_measurements_graph(measurements_history)
    
    return render_template('track.html', 
                         msg=msg,
                         exercise_types=exercise_types,
                         workout_history=workout_history,
                         weight_history=weight_history,
                         measurements_history=measurements_history,
                         weight_graph=weight_graph,
                         measurements_graph=measurements_graph,
                         start_date=start_date,
                         end_date=end_date)

def generate_weight_graph(weight_history):
    if not weight_history:
        return None
    
    # Sort data by date before plotting
    sorted_data = sorted(weight_history, key=lambda x: x['date_recorded'])
    dates = [record['date_recorded'].strftime('%d-%m-%Y') for record in sorted_data]
    weights = [float(record['weight']) for record in sorted_data]
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, weights, marker='o', linestyle='-')
    plt.title('Evolución del Peso')
    plt.xlabel('Fecha')
    plt.ylabel('Peso (kg)')
    plt.xticks(dates, rotation=45, ha='right')
    plt.grid(True)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return graph_url

def generate_measurements_graph(measurements_history):
    if not measurements_history:
        return None
    
    muscle_data = {}
    for record in measurements_history:
        muscle = record['muscle_group']
        if muscle not in muscle_data:
            muscle_data[muscle] = {
                'dates': [],
                'measurements': []
            }
        muscle_data[muscle]['dates'].append(record['date_recorded'])
        muscle_data[muscle]['measurements'].append(float(record['measurement']))
    
    plt.figure(figsize=(12, 8))
    
    for muscle, data in muscle_data.items():
        # Sort dates and measurements together
        sorted_pairs = sorted(zip(data['dates'], data['measurements']))
        sorted_dates = [date.strftime('%d-%m-%Y') for date, _ in sorted_pairs]
        sorted_measurements = [measurement for _, measurement in sorted_pairs]
        
        plt.plot(sorted_dates, sorted_measurements, marker='o', label=muscle, linestyle='-')
    
    plt.title('Evolución de Medidas')
    plt.xlabel('Fecha')
    plt.ylabel('Medida (cm)')
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.grid(True)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return graph_url

# Ruta-Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)