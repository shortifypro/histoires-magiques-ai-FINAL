from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, flash, send_file
import sqlite3
import hashlib
import os
import openai
from datetime import datetime, timedelta
import requests
import json
from fpdf import FPDF
import io
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'histoires-magiques-secret-key-2024')

# Configuration des APIs
openai.api_key = os.environ.get('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    
    # Table des utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        plan TEXT DEFAULT 'free',
        credits INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Table des histoires
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        child_name TEXT,
        theme TEXT,
        character_type TEXT,
        moral TEXT,
        age_range TEXT,
        audio_file TEXT,
        pdf_file TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Table des abonnements
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT NOT NULL,
        paypal_subscription_id TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

# Fonctions utilitaires
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_email(email):
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(email, password, name):
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                 (email, hash_password(password), name))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def generate_story_with_ai(child_name, theme, character_type, moral, age_range):
    try:
        prompt = f"""Créez une histoire magique pour enfants avec ces paramètres :
        - Nom de l'enfant : {child_name}
        - Thème : {theme}
        - Type de personnage : {character_type}
        - Morale à transmettre : {moral}
        - Tranche d'âge : {age_range}
        
        L'histoire doit être adaptée à l'âge, captivante, éducative et se terminer positivement.
        Longueur : environ 300-500 mots."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.8
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Il était une fois {child_name}, un enfant merveilleux qui aimait les aventures..."

def generate_audio_with_elevenlabs(text):
    if not ELEVENLABS_API_KEY:
        return None
    
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        return None

def create_pdf_story(title, content, child_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    
    # Titre
    pdf.cell(0, 10, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)
    
    # Contenu
    pdf.set_font("Arial", size=12)
    lines = content.split('\n')
    for line in lines:
        pdf.cell(0, 8, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# Routes principales
@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦊 Histoires Magiques - Créateur d'histoires pour enfants</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            overflow-x: hidden;
        }

        :root {
            --primary-purple: #8b5cf6;
            --primary-pink: #ec4899;
            --primary-orange: #f97316;
            --primary-yellow: #fbbf24;
            --soft-blue: #60a5fa;
            --soft-green: #34d399;
            --warm-white: #fef7ff;
            --text-dark: #1f2937;
            --text-light: #6b7280;
        }

        .header {
            background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-pink) 100%);
            padding: 1rem 0;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
        }

        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .nav-buttons {
            display: flex;
            gap: 1rem;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 25px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            font-size: 0.9rem;
            display: inline-block;
        }

        .btn-primary {
            background: var(--primary-orange);
            color: white;
        }

        .btn-primary:hover {
            background: #ea580c;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(249, 115, 22, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: white;
            color: var(--primary-purple);
        }

        .hero {
            background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-pink) 50%, var(--primary-orange) 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding-top: 80px;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="stars" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="rgba(255,255,255,0.3)"/></pattern></defs><rect width="100" height="100" fill="url(%23stars)"/></svg>');
            animation: twinkle 3s ease-in-out infinite alternate;
        }

        @keyframes twinkle {
            0% { opacity: 0.3; }
            100% { opacity: 0.8; }
        }

        .hero-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            position: relative;
            z-index: 2;
        }

        .hero-content h1 {
            font-size: 3.5rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }

        .hero-content p {
            font-size: 1.3rem;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        .hero-stats {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .stat {
            text-align: center;
            color: white;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .hero-image {
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        .hero-illustration {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, var(--primary-yellow) 0%, var(--primary-orange) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 8rem;
            animation: float 3s ease-in-out infinite;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        .how-it-works {
            padding: 6rem 0;
            background: var(--warm-white);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        .section-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 3rem;
        }

        .steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 3rem;
            margin-top: 4rem;
        }

        .step {
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .step:hover {
            transform: translateY(-10px);
        }

        .step-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
            font-weight: bold;
        }

        .step:nth-child(1) .step-icon {
            background: linear-gradient(135deg, var(--primary-purple), var(--primary-pink));
        }

        .step:nth-child(2) .step-icon {
            background: linear-gradient(135deg, var(--primary-pink), var(--primary-orange));
        }

        .step:nth-child(3) .step-icon {
            background: linear-gradient(135deg, var(--primary-orange), var(--primary-yellow));
        }

        .step h3 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-dark);
            margin-bottom: 1rem;
        }

        .step p {
            color: var(--text-light);
            line-height: 1.6;
        }

        .pricing {
            padding: 6rem 0;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        .pricing-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 4rem;
        }

        .pricing-card {
            background: white;
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .pricing-card:hover {
            transform: translateY(-10px);
        }

        .pricing-card.featured {
            border: 3px solid var(--primary-purple);
            transform: scale(1.05);
        }

        .pricing-card.featured::before {
            content: 'POPULAIRE';
            position: absolute;
            top: 20px;
            right: -30px;
            background: var(--primary-purple);
            color: white;
            padding: 0.5rem 2rem;
            font-size: 0.8rem;
            font-weight: 600;
            transform: rotate(45deg);
        }

        .plan-name {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-dark);
            margin-bottom: 1rem;
        }

        .plan-price {
            font-size: 3rem;
            font-weight: 700;
            color: var(--primary-purple);
            margin-bottom: 0.5rem;
        }

        .plan-period {
            color: var(--text-light);
            margin-bottom: 2rem;
        }

        .plan-features {
            list-style: none;
            margin-bottom: 2rem;
        }

        .plan-features li {
            padding: 0.5rem 0;
            color: var(--text-light);
        }

        .plan-features li::before {
            content: '✨';
            margin-right: 0.5rem;
        }

        .footer {
            background: var(--text-dark);
            color: white;
            padding: 3rem 0 1rem;
        }

        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            text-align: center;
        }

        .footer-logo {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .footer-text {
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 2rem;
        }

        .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .footer-links a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: color 0.3s ease;
        }

        .footer-links a:hover {
            color: var(--primary-purple);
        }

        .footer-bottom {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 1rem;
            color: rgba(255, 255, 255, 0.5);
        }

        @media (max-width: 768px) {
            .hero-container {
                grid-template-columns: 1fr;
                text-align: center;
            }

            .hero-content h1 {
                font-size: 2.5rem;
            }

            .hero-stats {
                justify-content: center;
            }

            .nav-container {
                padding: 0 1rem;
            }

            .nav-buttons {
                flex-direction: column;
                gap: 0.5rem;
            }

            .hero-illustration {
                width: 300px;
                height: 300px;
                font-size: 6rem;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <nav class="nav-container">
            <a href="{{ url_for('home') }}" class="logo">🦊 Histoires Magiques</a>
            <div class="nav-buttons">
                {% if 'user_id' in session %}
                    <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Mon compte</a>
                    <a href="{{ url_for('create_story') }}" class="btn btn-primary">Créer une histoire</a>
                {% else %}
                    <a href="{{ url_for('login') }}" class="btn btn-secondary">Se connecter</a>
                    <a href="{{ url_for('register') }}" class="btn btn-primary">Créer une histoire</a>
                {% endif %}
            </div>
        </nav>
    </header>

    <section class="hero">
        <div class="hero-container">
            <div class="hero-content">
                <h1>Créez des histoires magiques pour vos enfants</h1>
                <p>Transformez l'heure du coucher en moment extraordinaire avec des histoires personnalisées, générées par IA et racontées avec des voix enchantées.</p>
                
                <div class="hero-stats">
                    <div class="stat">
                        <span class="stat-number">10,000+</span>
                        <span class="stat-label">Histoires créées</span>
                    </div>
                    <div class="stat">
                        <span class="stat-number">5,000+</span>
                        <span class="stat-label">Familles heureuses</span>
                    </div>
                    <div class="stat">
                        <span class="stat-number">4.9/5</span>
                        <span class="stat-label">Note moyenne</span>
                    </div>
                </div>

                {% if 'user_id' in session %}
                    <a href="{{ url_for('create_story') }}" class="btn btn-primary" style="font-size: 1.1rem; padding: 1rem 2rem;">
                        ✨ Créer une nouvelle histoire
                    </a>
                {% else %}
                    <a href="{{ url_for('register') }}" class="btn btn-primary" style="font-size: 1.1rem; padding: 1rem 2rem;">
                        ✨ Créer ma première histoire gratuite
                    </a>
                {% endif %}
            </div>
            
            <div class="hero-image">
                <div class="hero-illustration">
                    🦊🌙
                </div>
            </div>
        </div>
    </section>

    <section class="how-it-works">
        <div class="container">
            <h2 class="section-title">Comment ça marche ?</h2>
            <div class="steps">
                <div class="step">
                    <div class="step-icon">✏️</div>
                    <h3>1. Personnalisez</h3>
                    <p>Choisissez le nom de votre enfant, ses personnages préférés, le thème de l'histoire et la morale à transmettre.</p>
                </div>
                <div class="step">
                    <div class="step-icon">🤖</div>
                    <h3>2. L'IA crée</h3>
                    <p>Notre intelligence artificielle génère une histoire unique, adaptée à l'âge de votre enfant avec des personnages attachants.</p>
                </div>
                <div class="step">
                    <div class="step-icon">🎧</div>
                    <h3>3. Écoutez & rêvez</h3>
                    <p>Recevez un fichier audio MP3 et un livret PDF magnifiquement illustré, prêts pour l'heure du coucher.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="pricing">
        <div class="container">
            <h2 class="section-title">Choisissez votre formule</h2>
            <div class="pricing-cards">
                <div class="pricing-card">
                    <h3 class="plan-name">Découverte</h3>
                    <div class="plan-price">Gratuit</div>
                    <div class="plan-period">Pour toujours</div>
                    <ul class="plan-features">
                        <li>3 histoires gratuites</li>
                        <li>Personnalisation basique</li>
                        <li>Audio MP3</li>
                        <li>Livret PDF</li>
                    </ul>
                    {% if 'user_id' not in session %}
                        <a href="{{ url_for('register') }}" class="btn btn-secondary">Commencer gratuitement</a>
                    {% else %}
                        <a href="{{ url_for('create_story') }}" class="btn btn-secondary">Créer une histoire</a>
                    {% endif %}
                </div>

                <div class="pricing-card featured">
                    <h3 class="plan-name">Starter</h3>
                    <div class="plan-price">12€</div>
                    <div class="plan-period">par mois</div>
                    <ul class="plan-features">
                        <li>Histoires illimitées</li>
                        <li>Personnalisation avancée</li>
                        <li>Choix de voix</li>
                        <li>Illustrations personnalisées</li>
                        <li>Bibliothèque privée</li>
                    </ul>
                    <a href="{{ url_for('subscribe', plan='starter') }}" class="btn btn-primary">Choisir Starter</a>
                </div>

                <div class="pricing-card">
                    <h3 class="plan-name">Family</h3>
                    <div class="plan-price">24€</div>
                    <div class="plan-period">par mois</div>
                    <ul class="plan-features">
                        <li>Tout du plan Starter</li>
                        <li>Jusqu'à 5 enfants</li>
                        <li>Histoires collaboratives</li>
                        <li>Support prioritaire</li>
                        <li>Accès anticipé aux nouveautés</li>
                    </ul>
                    <a href="{{ url_for('subscribe', plan='family') }}" class="btn btn-primary">Choisir Family</a>
                </div>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="footer-content">
            <div class="footer-logo">🦊 Histoires Magiques</div>
            <p class="footer-text">Créez des souvenirs magiques avec vos enfants, une histoire à la fois.</p>
            
            <div class="footer-links">
                <a href="#">À propos</a>
                <a href="#">Contact</a>
                <a href="#">Confidentialité</a>
                <a href="#">Conditions</a>
            </div>
            
            <div class="footer-bottom">
                <p>&copy; 2025 Histoires Magiques. Tous droits réservés.</p>
            </div>
        </div>
    </footer>
</body>
</html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        if get_user_by_email(email):
            flash('Cet email est déjà utilisé.')
            return redirect(url_for('register'))
        
        user_id = create_user(email, password, name)
        if user_id:
            session['user_id'] = user_id
            session['user_email'] = email
            session['user_name'] = name
            flash('Compte créé avec succès ! Vous avez 3 histoires gratuites.')
            return redirect(url_for('create_story'))
        else:
            flash('Erreur lors de la création du compte.')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscription - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .form-container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .form-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 2rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #374151;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .btn-submit {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
        }
        .form-footer {
            text-align: center;
            margin-top: 2rem;
        }
        .form-footer a {
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 600;
        }
        .alert {
            background: #fee2e2;
            color: #dc2626;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h1 class="form-title">🦊 Inscription</h1>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="name">Nom complet</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-submit">Créer mon compte</button>
        </form>
        
        <div class="form-footer">
            <p>Déjà un compte ? <a href="{{ url_for('login') }}">Se connecter</a></p>
            <p><a href="{{ url_for('home') }}">← Retour à l'accueil</a></p>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        if user and user[2] == hash_password(password):
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            session['user_name'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect.')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .form-container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .form-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 2rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #374151;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .btn-submit {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
        }
        .form-footer {
            text-align: center;
            margin-top: 2rem;
        }
        .form-footer a {
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 600;
        }
        .alert {
            background: #fee2e2;
            color: #dc2626;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h1 class="form-title">🦊 Connexion</h1>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-submit">Se connecter</button>
        </form>
        
        <div class="form-footer">
            <p>Pas encore de compte ? <a href="{{ url_for('register') }}">S'inscrire</a></p>
            <p><a href="{{ url_for('home') }}">← Retour à l'accueil</a></p>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/create_story', methods=['GET', 'POST'])
def create_story():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Vérifier les crédits
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    c.execute('SELECT credits, plan FROM users WHERE id = ?', (session['user_id'],))
    user_data = c.fetchone()
    conn.close()
    
    if not user_data:
        return redirect(url_for('login'))
    
    credits, plan = user_data
    
    if request.method == 'POST':
        if plan == 'free' and credits <= 0:
            flash('Vous n\'avez plus de crédits gratuits. Abonnez-vous pour continuer.')
            return redirect(url_for('home'))
        
        # Récupérer les données du formulaire
        child_name = request.form['child_name']
        theme = request.form['theme']
        character_type = request.form['character_type']
        moral = request.form['moral']
        age_range = request.form['age_range']
        
        # Générer l'histoire
        story_content = generate_story_with_ai(child_name, theme, character_type, moral, age_range)
        story_title = f"L'aventure de {child_name}"
        
        # Générer l'audio
        audio_content = generate_audio_with_elevenlabs(story_content)
        
        # Créer le PDF
        pdf_content = create_pdf_story(story_title, story_content, child_name)
        
        # Sauvegarder en base
        conn = sqlite3.connect('histoires_magiques.db')
        c = conn.cursor()
        c.execute('''INSERT INTO stories (user_id, title, content, child_name, theme, character_type, moral, age_range)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], story_title, story_content, child_name, theme, character_type, moral, age_range))
        story_id = c.lastrowid
        
        # Décrémenter les crédits si plan gratuit
        if plan == 'free':
            c.execute('UPDATE users SET credits = credits - 1 WHERE id = ?', (session['user_id'],))
        
        conn.commit()
        conn.close()
        
        # Stocker les fichiers en session pour téléchargement
        session[f'story_content_{story_id}'] = story_content
        session[f'pdf_content_{story_id}'] = base64.b64encode(pdf_content).decode()
        if audio_content:
            session[f'audio_content_{story_id}'] = base64.b64encode(audio_content).decode()
        
        return redirect(url_for('story_result', story_id=story_id))
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Créer une histoire - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            padding: 3rem;
        }
        .page-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 1rem;
        }
        .page-subtitle {
            text-align: center;
            color: #6b7280;
            margin-bottom: 3rem;
        }
        .credits-info {
            background: #f0f9ff;
            border: 2px solid #0ea5e9;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group.full-width {
            grid-column: 1 / -1;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #374151;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #8b5cf6;
        }
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        .btn-submit {
            width: 100%;
            padding: 1.5rem;
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
        }
        .back-link {
            display: inline-block;
            margin-bottom: 2rem;
            color: #8b5cf6;
            text-decoration: none;
            font-weight: 600;
        }
        @media (max-width: 768px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="{{ url_for('home') }}" class="back-link">← Retour à l'accueil</a>
        
        <h1 class="page-title">✨ Créer une histoire magique</h1>
        <p class="page-subtitle">Personnalisez chaque détail pour créer une histoire unique pour votre enfant</p>
        
        <div class="credits-info">
            <strong>💎 Crédits restants : {{ credits }}</strong>
            {% if plan == 'free' %}
                <p>Plan gratuit - {{ credits }} histoire(s) gratuite(s) restante(s)</p>
            {% else %}
                <p>Plan {{ plan }} - Histoires illimitées</p>
            {% endif %}
        </div>
        
        <form method="POST">
            <div class="form-grid">
                <div class="form-group">
                    <label for="child_name">Nom de l'enfant</label>
                    <input type="text" id="child_name" name="child_name" required placeholder="Ex: Emma, Lucas...">
                </div>
                
                <div class="form-group">
                    <label for="age_range">Âge de l'enfant</label>
                    <select id="age_range" name="age_range" required>
                        <option value="">Choisir l'âge</option>
                        <option value="3-5 ans">3-5 ans</option>
                        <option value="6-8 ans">6-8 ans</option>
                        <option value="9-12 ans">9-12 ans</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="theme">Thème de l'histoire</label>
                    <select id="theme" name="theme" required>
                        <option value="">Choisir un thème</option>
                        <option value="Aventure">🗺️ Aventure</option>
                        <option value="Amitié">👫 Amitié</option>
                        <option value="Nature">🌳 Nature</option>
                        <option value="Courage">💪 Courage</option>
                        <option value="Famille">👨‍👩‍👧‍👦 Famille</option>
                        <option value="Magie">✨ Magie</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="character_type">Type de personnage principal</label>
                    <select id="character_type" name="character_type" required>
                        <option value="">Choisir un personnage</option>
                        <option value="Animaux">🦊 Animaux</option>
                        <option value="Humains">👧 Humains</option>
                        <option value="Fantastiques">🧚 Créatures fantastiques</option>
                    </select>
                </div>
                
                <div class="form-group full-width">
                    <label for="moral">Morale ou valeur à transmettre</label>
                    <textarea id="moral" name="moral" required placeholder="Ex: L'importance de l'entraide, la persévérance, le respect de la nature..."></textarea>
                </div>
            </div>
            
            <button type="submit" class="btn-submit">🎨 Créer mon histoire magique</button>
        </form>
    </div>
</body>
</html>
    ''', credits=credits, plan=plan)

@app.route('/story_result/<int:story_id>')
def story_result(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Récupérer l'histoire
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    c.execute('SELECT * FROM stories WHERE id = ? AND user_id = ?', (story_id, session['user_id']))
    story = c.fetchone()
    conn.close()
    
    if not story:
        return redirect(url_for('home'))
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Votre histoire - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            padding: 3rem;
        }
        .success-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .success-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .success-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 1rem;
        }
        .story-title {
            font-size: 2rem;
            font-weight: 600;
            color: #8b5cf6;
            margin-bottom: 2rem;
            text-align: center;
        }
        .story-content {
            background: #f8fafc;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            line-height: 1.8;
            font-size: 1.1rem;
        }
        .download-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .download-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 1rem;
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: transform 0.3s ease;
        }
        .download-btn:hover {
            transform: translateY(-2px);
        }
        .download-btn.audio {
            background: linear-gradient(135deg, #f97316, #fbbf24);
        }
        .actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
        }
        .btn-secondary {
            background: #e5e7eb;
            color: #374151;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        @media (max-width: 768px) {
            .download-section {
                grid-template-columns: 1fr;
            }
            .actions {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-header">
            <div class="success-icon">🎉</div>
            <h1 class="success-title">Votre histoire est prête !</h1>
            <p>Une histoire magique créée spécialement pour {{ story[4] }}</p>
        </div>
        
        <h2 class="story-title">{{ story[1] }}</h2>
        
        <div class="story-content">
            {{ story[2]|replace('\n', '<br>')|safe }}
        </div>
        
        <div class="download-section">
            <a href="{{ url_for('download_pdf', story_id=story[0]) }}" class="download-btn">
                📄 Télécharger le PDF
            </a>
            {% if session.get('audio_content_' + story[0]|string) %}
                <a href="{{ url_for('download_audio', story_id=story[0]) }}" class="download-btn audio">
                    🎵 Télécharger l'audio
                </a>
            {% else %}
                <div class="download-btn audio" style="opacity: 0.5; cursor: not-allowed;">
                    🎵 Audio non disponible
                </div>
            {% endif %}
        </div>
        
        <div class="actions">
            <a href="{{ url_for('create_story') }}" class="btn btn-primary">Créer une nouvelle histoire</a>
            <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">Mes histoires</a>
        </div>
    </div>
</body>
</html>
    ''', story=story)

@app.route('/download_pdf/<int:story_id>')
def download_pdf(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    pdf_content = session.get(f'pdf_content_{story_id}')
    if not pdf_content:
        return redirect(url_for('home'))
    
    pdf_bytes = base64.b64decode(pdf_content)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'histoire_{story_id}.pdf'
    )

@app.route('/download_audio/<int:story_id>')
def download_audio(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    audio_content = session.get(f'audio_content_{story_id}')
    if not audio_content:
        return redirect(url_for('home'))
    
    audio_bytes = base64.b64decode(audio_content)
    
    return send_file(
        io.BytesIO(audio_bytes),
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name=f'histoire_{story_id}.mp3'
    )

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Récupérer les informations utilisateur
    conn = sqlite3.connect('histoires_magiques.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    
    # Récupérer les histoires
    c.execute('SELECT * FROM stories WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (session['user_id'],))
    stories = c.fetchall()
    
    conn.close()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mon compte - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            padding: 3rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
        }
        .welcome {
            font-size: 2rem;
            font-weight: 700;
            color: #1f2937;
        }
        .user-info {
            background: #f0f9ff;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 3rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
        }
        .info-item {
            text-align: center;
        }
        .info-label {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 0.5rem;
        }
        .info-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 2rem;
        }
        .stories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .story-card {
            background: #f8fafc;
            padding: 2rem;
            border-radius: 15px;
            border: 2px solid #e5e7eb;
            transition: transform 0.3s ease;
        }
        .story-card:hover {
            transform: translateY(-5px);
            border-color: #8b5cf6;
        }
        .story-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1rem;
        }
        .story-meta {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 1rem;
        }
        .story-actions {
            display: flex;
            gap: 0.5rem;
        }
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            font-size: 0.9rem;
            transition: transform 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
        }
        .btn-secondary {
            background: #e5e7eb;
            color: #374151;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }
        .btn-large {
            padding: 1rem 2rem;
            font-size: 1.1rem;
        }
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="welcome">Bonjour {{ user[3] }} ! 👋</h1>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Se déconnecter</a>
        </div>
        
        <div class="user-info">
            <div class="info-item">
                <div class="info-label">Plan actuel</div>
                <div class="info-value">{{ user[4].title() }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Crédits restants</div>
                <div class="info-value">
                    {% if user[4] == 'free' %}
                        {{ user[5] }}
                    {% else %}
                        ∞
                    {% endif %}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Histoires créées</div>
                <div class="info-value">{{ stories|length }}</div>
            </div>
        </div>
        
        <h2 class="section-title">📚 Mes dernières histoires</h2>
        
        {% if stories %}
            <div class="stories-grid">
                {% for story in stories %}
                    <div class="story-card">
                        <h3 class="story-title">{{ story[1] }}</h3>
                        <div class="story-meta">
                            Pour {{ story[4] }} • {{ story[5] }} • {{ story[11][:10] }}
                        </div>
                        <div class="story-actions">
                            <a href="{{ url_for('story_result', story_id=story[0]) }}" class="btn btn-primary">Voir</a>
                            <a href="{{ url_for('download_pdf', story_id=story[0]) }}" class="btn btn-secondary">PDF</a>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="empty-state">
                <p>Vous n'avez pas encore créé d'histoire.</p>
                <p>Commencez dès maintenant !</p>
            </div>
        {% endif %}
        
        <div class="actions">
            <a href="{{ url_for('create_story') }}" class="btn btn-primary btn-large">✨ Créer une nouvelle histoire</a>
            <a href="{{ url_for('home') }}" class="btn btn-secondary btn-large">← Retour à l'accueil</a>
        </div>
    </div>
</body>
</html>
    ''', user=user, stories=stories)

@app.route('/subscribe/<plan>')
def subscribe(plan):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    plans = {
        'starter': {'name': 'Starter', 'price': 12},
        'family': {'name': 'Family', 'price': 24}
    }
    
    if plan not in plans:
        return redirect(url_for('home'))
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abonnement {{ plan_info.name }} - Histoires Magiques</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        .subscription-container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 500px;
            text-align: center;
        }
        .plan-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 1rem;
        }
        .plan-price {
            font-size: 3rem;
            font-weight: 700;
            color: #8b5cf6;
            margin-bottom: 2rem;
        }
        .plan-features {
            list-style: none;
            margin-bottom: 3rem;
            text-align: left;
        }
        .plan-features li {
            padding: 0.5rem 0;
            color: #374151;
        }
        .plan-features li::before {
            content: '✨';
            margin-right: 0.5rem;
        }
        .paypal-info {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            font-size: 1.1rem;
            transition: transform 0.3s ease;
            margin: 0.5rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            color: white;
        }
        .btn-secondary {
            background: #e5e7eb;
            color: #374151;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="subscription-container">
        <h1 class="plan-title">Plan {{ plan_info.name }}</h1>
        <div class="plan-price">{{ plan_info.price }}€<span style="font-size: 1rem; color: #6b7280;">/mois</span></div>
        
        <ul class="plan-features">
            <li>Histoires illimitées</li>
            <li>Personnalisation avancée</li>
            <li>Choix de voix</li>
            <li>Illustrations personnalisées</li>
            <li>Bibliothèque privée</li>
            {% if plan == 'family' %}
                <li>Jusqu'à 5 enfants</li>
                <li>Histoires collaboratives</li>
                <li>Support prioritaire</li>
            {% endif %}
        </ul>
        
        <div class="paypal-info">
            <h3>💳 Paiement sécurisé avec PayPal</h3>
            <p>Abonnement mensuel - Annulation possible à tout moment</p>
        </div>
        
        <div id="paypal-button-container"></div>
        
        <div style="margin-top: 2rem;">
            <a href="{{ url_for('home') }}" class="btn btn-secondary">← Retour</a>
        </div>
    </div>
    
    <script>
        // Simulation PayPal (remplacer par vraie intégration)
        document.getElementById('paypal-button-container').innerHTML = 
            '<button class="btn btn-primary" onclick="simulatePayment()">💳 S\'abonner avec PayPal</button>';
        
        function simulatePayment() {
            alert('Fonctionnalité PayPal en cours d\'intégration. Votre abonnement sera activé prochainement !');
            window.location.href = '{{ url_for("dashboard") }}';
        }
    </script>
</body>
</html>
    ''', plan=plan, plan_info=plans[plan])

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

