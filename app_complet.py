from flask import Flask, render_template_string
import os

app = Flask(__name__)

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

        /* Variables CSS pour les couleurs */
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

        /* Header */
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

        /* Hero Section */
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

        /* How It Works Section */
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

        /* Pricing Section */
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

        /* Footer */
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

        /* Responsive */
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
    <!-- Header -->
    <header class="header">
        <nav class="nav-container">
            <a href="#" class="logo">🦊 Histoires Magiques</a>
            <div class="nav-buttons">
                <a href="#" class="btn btn-secondary">Se connecter</a>
                <a href="#" class="btn btn-primary">Créer une histoire</a>
            </div>
        </nav>
    </header>

    <!-- Hero Section -->
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

                <a href="#" class="btn btn-primary" style="font-size: 1.1rem; padding: 1rem 2rem;">
                    ✨ Créer ma première histoire gratuite
                </a>
            </div>
            
            <div class="hero-image">
                <div class="hero-illustration">
                    🦊🌙
                </div>
            </div>
        </div>
    </section>

    <!-- How It Works -->
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

    <!-- Pricing -->
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
                    <a href="#" class="btn btn-secondary">Commencer gratuitement</a>
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
                    <a href="#" class="btn btn-primary">Choisir Starter</a>
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
                    <a href="#" class="btn btn-primary">Choisir Family</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

