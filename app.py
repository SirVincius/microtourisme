import hashlib
import uuid
from flask import Flask, jsonify, redirect, render_template, request, url_for, g, session, flash
from flask_session import Session
from flask_mail import Mail, Message
import requests
from babel.dates import format_datetime
from datetime import datetime, timedelta
from form import AccountForm, LoginForm, GenerationForm, ResetRequestForm
from database import Database
import json


import geocoder


app = Flask(__name__)
app.config['SECRET_KEY'] = 'fdhdsf78dhfds87hf8dshfdnv77234234754nfd987fa'
app.config['SESSION_TYPE'] = 'filesystem'
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'MicroTourisme00@outlook.com'
app.config['MAIL_PASSWORD'] = 'MicroTourism00$'

mail = Mail(app)


# Initialisation des sessions
Session(app)


#fonction pour meteo pour 3 jours
def get_three_days_weather(latitude=0, longitude=0):
    weather = {
        'today': get_hourly_weather(latitude, longitude, 0),
        'tomorrow': get_hourly_weather(latitude, longitude, 1),
        'day_after_tomorrow': get_hourly_weather(latitude, longitude, 2)
    }
    return weather

#fonction pour obtenir la meteo pour chaque heure du jour selectionné par get_three_days_weather
def get_hourly_weather(longitude, latitude, day_offset=0):

    url = f"http://api.weatherapi.com/v1/forecast.json?key=INSERTKEY&q={latitude},{longitude}&days=3"
    response = requests.get(url)
    data = response.json()
    current_time = datetime.now() + timedelta(days=day_offset)
    hourly_weather = []
    cutoff_time = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    forecast_day = data['forecast']['forecastday'][day_offset]
    
    for hour in forecast_day['hour']:
        time = datetime.strptime(hour['time'], '%Y-%m-%d %H:%M')
        
        if day_offset == 0 and time < current_time:
            continue
        
        weather = {
            'time': 'Maintenant' if day_offset == 0 and len(hourly_weather) == 0 else time.strftime('%H:%M'),
            'weekday': format_datetime(time, 'EEEE', locale='fr_FR'),
            'temperature': int(float(hour['temp_c'])),
            'condition': hour['condition']['text'],
            'icon': hour['condition']['icon'],
            'is_now': day_offset == 0 and len(hourly_weather) == 0
        }
        hourly_weather.append(weather)
        if len(hourly_weather) >= 24:
                return hourly_weather

    if len(hourly_weather) < 24 and day_offset == 0:
        next_day_url = f'http://api.weatherapi.com/v1/forecast.json?key=INSERTKEY&q={latitude},{longitude}&days=2'
        next_day_response = requests.get(next_day_url)
        next_day_data = next_day_response.json()
        for day in next_day_data['forecast']['forecastday'][1:]:
            for hour in day['hour']:
                time = datetime.strptime(hour['time'], '%Y-%m-%d %H:%M')
                if time.hour == 0 or len(hourly_weather) > 0:
                    if len(hourly_weather) < 24:
                        weather = {
                            'time': time.strftime('%H:%M'),
                            'weekday': format_datetime(time, 'EEEE', locale='fr_FR'),
                            'temperature': int(float(hour['temp_c'])),
                            'condition': hour['condition']['text'],
                            'icon': hour['condition']['icon'],
                            'is_now': False
                        }
                        hourly_weather.append(weather)

    return hourly_weather





# Fonction pour envoyer l'e-mail de réinitialisation de mot de passe
def send_reset_email(user_email):
    msg = Message('Demande de réinitialisation de mot de passe', sender='MicroTourisme00@outlook.com', recipients=[user_email])
    msg.body = f'''Pour réinitialiser votre mot de passe, visitez le lien suivant:
{url_for('reset_password_form', email=user_email, _external=True)}

Si vous n'avez pas fait cette demande, ignorez cet e-mail et aucune modification ne sera apportée.
'''
    mail.send(msg)

    
#email de confirmation a l'inscription
def send_confirmation_email(user_email, confirm_url):
    msg = Message('Confirmez votre email', sender='MicroTourisme00@outlook.com', recipients=[user_email])
    msg.body = f'''Pour confirmer votre email, visitez le lien suivant:
{confirm_url}

Si vous n'avez pas créé ce compte, ignorez cet email.
'''
    mail.send(msg)




# Se déconnecter de la base de données
def deconnection():
    with app.app_context():
        database = getattr(g, "_database", None)
        if database is not None:
            database.deconnection()


def curll(o_lat, o_lng, d_lat, d_lng, deplacement):

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': 'INSERT KEY',
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.polyline,routes.legs.travelAdvisory,routes.legs.steps.navigationInstruction',
    }

    json_data = {
        'origin': {
            'location': {
                'latLng': {
                    'latitude': o_lat,
                    'longitude': o_lng,
                },
            },
        },
        'destination': {
            'location': {
                'latLng': {
                    'latitude': d_lat,
                    'longitude': d_lng,
                },
            },
        },
        'extraComputations': 'TRAFFIC_ON_POLYLINE',
        'routingPreference': 'TRAFFIC_AWARE_OPTIMAL',
        'travelMode': deplacement,
        'computeAlternativeRoutes': False,
        'routeModifiers': {
            'avoidTolls': False,
            'avoidHighways': False,
            'avoidFerries': False,
        },
        'languageCode': 'en-US',
        'units': 'IMPERIAL',
    }

    response = requests.post('https://routes.googleapis.com/directions/v2:computeRoutes', headers=headers, json=json_data)

    # Note: json_data will not be serialized by requests
    # exactly as it was in the original request.
    #data = '{\n  "origin":{\n    "location":{\n      "latLng":{\n        "latitude": 37.419734,\n        "longitude": -122.0827784\n      }\n    }\n  },\n  "destination":{\n    "location":{\n      "latLng":{\n        "latitude": 37.417670,\n        "longitude": -122.079595\n      }\n    }\n  },\n  "travelMode": "DRIVE",\n  "routingPreference": "TRAFFIC_AWARE",\n  "departureTime": "2023-10-15T15:01:23.045123456Z",\n  "computeAlternativeRoutes": false,\n  "routeModifiers": {\n    "avoidTolls": false,\n    "avoidHighways": false,\n    "avoidFerries": false\n  },\n  "languageCode": "en-US",\n  "units": "IMPERIAL"\n}'
    #response = requests.post('https://routes.googleapis.com/directions/v2:computeRoutes', headers=headers, data=data)

    return response

def curll2(o_lat, o_lng, d_lat, d_lng, deplacement):

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': 'INSERT KEY',
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.polyline,routes.legs.travelAdvisory,routes.legs.steps.navigationInstruction',
    }

    json_data = {
        'origin': {
            'location': {
                'latLng': {
                    'latitude': o_lat,
                    'longitude': o_lng,
                },
            },
        },
        'destination': {
            'location': {
                'latLng': {
                    'latitude': d_lat,
                    'longitude': d_lng,
                },
            },
        },
        'travelMode': deplacement,
        'computeAlternativeRoutes': False,
        'routeModifiers': {
            'avoidTolls': False,
            'avoidHighways': False,
            'avoidFerries': False,
        },
        'languageCode': 'en-US',
        'units': 'IMPERIAL',
    }

    response = requests.post('https://routes.googleapis.com/directions/v2:computeRoutes', headers=headers, json=json_data)

    # Note: json_data will not be serialized by requests
    # exactly as it was in the original request.
    #data = '{\n  "origin":{\n    "location":{\n      "latLng":{\n        "latitude": 37.419734,\n        "longitude": -122.0827784\n      }\n    }\n  },\n  "destination":{\n    "location":{\n      "latLng":{\n        "latitude": 37.417670,\n        "longitude": -122.079595\n      }\n    }\n  },\n  "travelMode": "DRIVE",\n  "routingPreference": "TRAFFIC_AWARE",\n  "departureTime": "2023-10-15T15:01:23.045123456Z",\n  "computeAlternativeRoutes": false,\n  "routeModifiers": {\n    "avoidTolls": false,\n    "avoidHighways": false,\n    "avoidFerries": false\n  },\n  "languageCode": "en-US",\n  "units": "IMPERIAL"\n}'
    #response = requests.post('https://routes.googleapis.com/directions/v2:computeRoutes', headers=headers, data=data)

    return response
##############################################################################
#                                                                            #
#                    SECTION POUR LES ROUTES                                 #
#                                                                            #
##############################################################################

# Affiche la page principale
@app.route('/')
def home():
    return render_template('home.html')


#afficher meteo
@app.route('/meteo')
def meteo():
    weather = get_three_days_weather()

    return render_template('meteo.html', weather=weather)




# Envoie le formulaire de création de compte utilisateur pour traitement
@app.route('/create_account', methods=['POST'])
def create_account():
    form = AccountForm()
    if form.validate_on_submit():
        firstname = form.firstName.data
        name = form.name.data
        birthdate = form.birthdate.data
        email = form.email.data
        password = form.password.data


        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(str(password + salt).encode("utf-8")).hexdigest()

        try:
            Database.get_db().create_user(firstname, name, birthdate, email, salt, hashed_password)
              # Send confirmation email
            confirm_url = url_for('confirm_email', email=email, _external=True)
            send_confirmation_email(email, confirm_url)
            return render_template('check_email.html')
        except Exception as e:
            print(f"Error during account creation: {e}")
            message = "Une erreur s'est produite pendant la création du compte."
            return redirect(url_for('error', message=message))

    return render_template("create_account.html", form = form)

#courriel de confirmation 
@app.route('/confirm_email')
def confirm_email():
    email = request.args.get('email')
    if not email:
        flash('Lien de confirmation invalide.', 'danger')
        return redirect(url_for('error', message='Lien de confirmation invalide.'))
    
    user = Database.get_db().get_user(email)
    if user and not user['confirmed']:
        Database.get_db().confirm_user_email(email)
        message = "Votre compte a été créé avec succès!"
        return render_template('confirmation.html', message=message)
    elif user and user['confirmed']:
        flash('Votre email est déjà confirmé.', 'info')
        return render_template('confirmation.html')
    else:
        flash('Lien de confirmation invalide.', 'danger')
        return redirect(url_for('error', message='Lien de confirmation invalide.'))
    

# Affiche la page de création de compte utilisateur
@app.route('/create_account', methods=['GET'])
def create_account_get():
    form = AccountForm()
    return render_template('create_account.html', form = form)


# Soumet les informations de connexion pour approbation
@app.route("/login", methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        
        user = Database.get_db().get_user(email)
        if user:
            salt = user['salt']
            hashed_password = hashlib.sha512(str(password + salt).encode("utf-8")).hexdigest()
            
            if hashed_password == user['hash']:
                if not user['confirmed']:
                    flash('Votre email n\'est pas confirmé. Veuillez vérifier votre email.', 'warning')
                    return redirect(url_for('login_get'))
                session['user'] = user['firstname']
                session['email'] = user['email']
                session['user_id'] = user['id']
                session['admin'] = user['admin']
                message = "Vous êtes maintenant connecté(e)."
                return render_template('connecte.html', message=message)
        
        message = "Nom d'utilisateur ou mot de passe incorrect."
        return redirect(url_for('error', message=message))
    else:
        return render_template('login.html', form=form)
 


# Affiche la page de connexion
@app.route("/login", methods=['GET'])
def login_get():
    form = LoginForm()
    return render_template('login.html', form = form)

#Se déconnecter
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# Affiche une page pour tester des trucs #TODO SUPPRIMER À LA TOUTE FIN
@app.route("/tests")
def tests():
    return render_template('tests.html')

#renitialisation mot de passe
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if 'user' in session:
        return redirect(url_for('home'))
    form = ResetRequestForm()
    if form.validate_on_submit():
        user = Database.get_db().get_user(form.email.data)
        if user:
            send_reset_email(user['email'])
        
        return render_template('check_email.html')
    return render_template('reset_request.html', form=form)

# Route pour réinitialiser le mot de passe
@app.route('/reset_password_form', methods=['GET', 'POST'])
def reset_password_form():
    email = request.args.get('email')
    if not email:
        flash('Adresse e-mail non valide.', 'danger')
        return redirect(url_for('reset_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password == confirm_password:
            # Generate a new salt
            new_salt = uuid.uuid4().hex
            # Hash the password with the new salt
            hashed_password = hashlib.sha512(str(password + new_salt).encode("utf-8")).hexdigest()
            # Update the password and salt in the database
            Database.get_db().update_password(email, hashed_password, new_salt)
            flash('Votre mot de passe a été mis à jour!', 'success')
            return render_template('reset_success.html')
        else:
            flash('Les mots de passe ne correspondent pas.', 'danger')
    return render_template('reset_password.html')


# Supprime les informations d'un utilisateur dans la base de données
@app.route("/delete_user", methods=['POST'])
def delete_user_admin():
    try:
        data = request.json
        Database.get_db().delete_user(data.get('courriel'))
        message = "Le compte a été supprimé avec succès!"
        return redirect(url_for('confirmation', message=message))
    except Exception as e:
        print(f"Error: {e}")
        message = "Une erreur s'est produite pendant la suppression du compte"
        return redirect(url_for('error', message=message))





# Envoie et traite le formulaire de génération de trajets
@app.route("/generation", methods=['POST'])
def generation():
    form = GenerationForm()
    return render_template('generation.html', form = form)

@app.route("/compte", methods=['GET'])
def compte():
    admin = session['admin']
    return render_template('compte.html', admin = admin)


# affiche le trajet test
@app.route("/trajets", methods=['POST'])
def trajets():
    form = GenerationForm()


    ###################################
    # Gestion des choix d'attractions #
    ###################################
    att1 = form.attraction1.data
    att2 = form.attraction2.data
    att3 = form.attraction3.data
    att4 = form.attraction4.data
    att5 = form.attraction5.data
    att6 = form.attraction6.data
    attractions = [att1, att2, att3, att4, att5, att6]
    deplacement = form.Deplacement.data
    rayon = form.rayon

    ###########################
    #  Gestion de la position #
    ###########################
    coordonnees = form.coordonnees.data
    lng = 0
    lat = 0

    # Coordonnees sprint 1
    if(coordonnees == '1'):
        lng = 45.5
        lat = -73.58
    
    # Coordonnees de la position actuelle
    if(coordonnees == '2'):
        g = geocoder.ip('me')
        lng = float(g.lat)
        lat = float(g.lng)

    if(coordonnees == '3'):
        ville = form.ville.data
        latlng = ville.split(";")
        lat = float(latlng[1])
        lng = float(latlng[0])


    #####################
    #  Gestion du rayon #
    #####################
    rayon = form.rayon.data

    ##############################
    #  Gestion de l'optimisation #
    ##############################
    optimisation = form.Optimisation.data

    return render_template('trajets.html', form = form, rayon=rayon,
        lng=lng, lat=lat, attractions = json.dumps(attractions), Deplacement=deplacement,
        optimisation = optimisation)


# Affiche le formulaire de génération de trajet
@app.route("/generation", methods=['GET'])
def generation_get():
    if 'user' not in session:
        return redirect(url_for('login_get'))
    form = GenerationForm()
    return render_template('generation.html', form = form)

@app.route("/path", methods=['POST'])
def path():

    optimisation = request.form['optimisation']
    dataTrajets = request.form['dataTrajets']
    rayon = request.form['rayon']
    deplacement = request.form['Deplacement']
    lat = request.form['lat']
    lng = request.form['lng']
    weather = get_three_days_weather(lat, lng)

    
    dataArray = dataTrajets.split(';')

    dataFinale = []
    listeOrdonnancementNombre = []
    travelAdvisory = []
    navigation = ""
     
    nbrAttractions = int(dataArray[len(dataArray)-1])

    for i in range(nbrAttractions):
            nn = "Attraction_" + str(i)
            if request.form.get(nn):
                listeOrdonnancementNombre.append(int(request.form.get(nn)))
                print(int(request.form.get(nn)))

    listeSansDoublons = []
    
    if(optimisation == 'Choix'):                 

        for i in range(nbrAttractions):
            cntr = 0
            for j in range(i, nbrAttractions):

                if(i != j and listeOrdonnancementNombre[i] == listeOrdonnancementNombre[j]):
                    cntr = cntr + 1
            
            if(cntr == 0): listeSansDoublons.append(listeOrdonnancementNombre[i])


        for i in range(len(listeSansDoublons)-1):
                
            d_lat = dataArray[listeSansDoublons[i]].split('::')[0]
            d_lng = dataArray[listeSansDoublons[i]].split('::')[1]
            
            a_lat = dataArray[listeSansDoublons[i+1]].split('::')[0]
            a_lng = dataArray[listeSansDoublons[i+1]].split('::')[1]

            if(deplacement == "DRIVE"):
                
                y = curll(d_lat, d_lng, a_lat, a_lng, deplacement)


                yy = json.loads(y.text)


                varY = yy['routes'][0]['polyline']['encodedPolyline']
                varZ = yy['routes'][0]['legs'][0]['travelAdvisory']['speedReadingIntervals']
                varI = yy['routes'][0]['legs'][0]['steps']

                FFF = ""

                for uu in range(0,len(varY)):

                    if(varY[uu] == '\\'):
                        
                        FFF+="É"
                    else: FFF+=varY[uu]

                dataFinale.append(FFF)

                travelAdvisory.append(varZ)

                FFF = ""

                for uu in range(0,len(varI)):

                    if ("navigationInstruction" in varI[uu]):

                        for uuu in range(0, len(varI[uu]['navigationInstruction']['instructions'])):

                            if(varI[uu]['navigationInstruction']['instructions'][uuu] == '\n'):
                
                                FFF+="ÉÉ"
                            
                            elif (varI[uu]['navigationInstruction']['instructions'][uuu] == '\''):
                                
                                FFF += "ÉÉÉ"

                            else:
                                
                                FFF+=varI[uu]['navigationInstruction']['instructions'][uuu]

                        FFF+="{"
                
                navigation+=FFF

            else:

                y = curll2(d_lat, d_lng, a_lat, a_lng, deplacement)


                yy = json.loads(y.text)


                varY = yy['routes'][0]['polyline']['encodedPolyline']

                FFF = ""

                for uu in range(0,len(varY)):

                    if(varY[uu] == '\\'):
                        
                        FFF+="É"
                    else: FFF+=varY[uu]

                dataFinale.append(FFF)

                

        listeOrdonnancementNombre = listeSansDoublons

    if(optimisation == 'distance'):

        dataFinale2 = []

        dataOrder = []  

        dataOrder2 = []

        dataOrder3 = []  

        already_found = [0]   
        
        for i in range(0,nbrAttractions-1):
            
            distance_min = 999999
            next_shortest_attraction = 0
            listeSansDoublons.append(i)
            
            d_lat = dataArray[already_found[len(already_found)-1]].split('::')[0]
            d_lng = dataArray[already_found[len(already_found)-1]].split('::')[1]
            
            for j in range(1, nbrAttractions):
                
                test = True
                
                for k in range(0, len(already_found)):
                    if(already_found[k] == j): test = False

                if(test):

                    a_lat = dataArray[j].split('::')[0]
                    a_lng = dataArray[j].split('::')[1]

                    

                    if(deplacement == "DRIVE"):

                        y = curll(d_lat, d_lng, a_lat, a_lng, deplacement)

                        yy = json.loads(y.text)

                        print(yy)

                        varZ = yy['routes'][0]['legs'][0]['travelAdvisory']['speedReadingIntervals']

                        varI = yy['routes'][0]['legs'][0]['steps']

                        distance = yy['routes'][0]['distanceMeters']

                        if(distance < distance_min):

                            distance_min = distance

                            varY = yy['routes'][0]['polyline']['encodedPolyline']
                            
                            FFF = ""

                            for uu in range(0,len(varY)):

                                if(varY[uu] == '\\'):
                                    
                                    FFF+="É"
                                else: FFF+=varY[uu]

                            dataFinale2.append(FFF)
                            dataOrder.append(distance)
                            dataOrder2.append(varZ)

                            FFF = ""
                            
                            for uu in range(0,len(varI)):

                                if ("navigationInstruction" in varI[uu]):

                                    for uuu in range(0, len(varI[uu]['navigationInstruction']['instructions'])):

                                        if(varI[uu]['navigationInstruction']['instructions'][uuu] == '\n'):
                            
                                            FFF+="ÉÉ"
                                        
                                        elif (varI[uu]['navigationInstruction']['instructions'][uuu] == '\''):
                                            
                                            FFF += "ÉÉÉ"

                                        else:
                                            
                                            FFF+=varI[uu]['navigationInstruction']['instructions'][uuu]

                                    FFF+="{"

                            dataOrder3.append(FFF)

                            next_shortest_attraction = j
                            listeSansDoublons.append(j)     
                        
                    else:

                        y = curll2(d_lat, d_lng, a_lat, a_lng, deplacement)

                        yy = json.loads(y.text)

                        print(yy)

                        distance = yy['routes'][0]['distanceMeters']

                        if(distance < distance_min):

                            distance_min = distance

                            varY = yy['routes'][0]['polyline']['encodedPolyline']
                            
                            FFF = ""

                            for uu in range(0,len(varY)):

                                if(varY[uu] == '\\'):
                                    
                                    FFF+="É"
                                else: FFF+=varY[uu]

                            dataFinale2.append(FFF)
                            dataOrder.append(distance)

                            next_shortest_attraction = j
                            listeSansDoublons.append(j)  



            yyy = 0

            for u in range(len(dataFinale2)):

                if(dataOrder[u] == distance_min): yyy = u

            dataFinale.append(dataFinale2[yyy])
            if(deplacement == "DRIVE"): travelAdvisory.append(dataOrder2[yyy])
            if(deplacement == "DRIVE"): navigation += dataOrder3[yyy]
            already_found.append(next_shortest_attraction)            

        listeOrdonnancementNombre = listeSansDoublons

    poly = json.dumps(dataFinale, ensure_ascii=False)

    liste = json.dumps(listeOrdonnancementNombre)

    travelAd = json.dumps(travelAdvisory)

    nav = navigation

    print(nav)

    success = Database.get_db().sauvegarder_trajet(lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather, session['user_id'])
    if not success:
        message = "Erreur lors de l'écriture dans la base de données"
        return render_template('error.html', message = message)
    else:
        return render_template('path.html', lng=lat, lat=lng, nav=nav, data = dataTrajets, rayon=rayon, polylines = poly, travelAdvisory = travelAd, coords = json.dumps(listeOrdonnancementNombre), weather = weather)

@app.route('/regenerer/<id>')
def regenerer(id):
    chemin = Database.get_db().obtenir_trajets_par_id(id)
    lat = chemin[1]
    print(lat)
    print("\n")
    lng = chemin[2]
    print(lng)
    print("\n")
    nav = chemin[3]
    print(nav)
    print("\n")
    dataTrajets = chemin[4]
    print(dataTrajets)
    print("\n")
    rayon = chemin[5]
    print(rayon)
    print("\n")
    poly = chemin[6]
    print(poly)
    print("\n")
    liste = json.loads(chemin[8])
    print(liste)
    print("\n")
    travelAd = chemin[7]
    print(travelAd)
    weather = get_three_days_weather(lat, lng)
    return render_template('path.html', lng=lat, lat=lng, nav=nav, data = dataTrajets, rayon=rayon, polylines = poly, travelAd = travelAd, coords = json.dumps(liste), weather = weather)

    

# Récupère les informations liées à un commentaire et les enregistre dans la base de données
@app.route('/commentaire', methods=['POST'])
def commentaire():

    data = request.json

    est_satisfait = data.get('est_satisfait')
    commentaire = data.get('commentaire')
    user_id = session['user_id']
    succes = Database.get_db().ajouter_commentaire(est_satisfait, commentaire, user_id)
    if succes:
        return jsonify({'status': 'success', 'est_satisfait': est_satisfait, 'commentaire': commentaire}), 200
    else:
        return jsonify({"erreur": "Echec de l'ajout de commentaire."}), 500



# Prend un message en paramètre et affiche celui-ci dans une page avec un lien
# de retour vers la page d'accueil
@app.route("/confirmation/<message>")
def confirmation(message):
    return render_template('confirmation.html', message=message)


@app.route('/error/<message>')
def error(message):
    return render_template('error.html', message=message)

@app.route("/obtenir_liste_commentaires")
def obtenir_liste_commentaires():
    try:
        commentaires = Database.get_db().obtenir_liste_commentaires()
        liste_commentaires = []
        for c in commentaires :
            dict = {'id' : str(c[0]), 'date' : str(c[1]), 'est_satisfait' : str(c[2]), 'commentaire' : c[3], 'user_id' : str(c[4])}
            liste_commentaires.append(dict)
        return liste_commentaires
    except Exception as e:
        print(f"Error: {e}")
        message = "Une erreur s'est produite pendant l'obtention de la liste des commentaires."
        return redirect(url_for('error', message=message))


@app.route("/obtenir_liste_comptes")
def obtenir_liste_comptes():
    try:
        comptes = Database.get_db().obtenir_liste_comptes()
        liste_comptes = []
        for c in comptes :
            dict = {'id' : str(c[0]), 'firstname' : c[1], 'name' : c[2], 'email' : c[3]}
            liste_comptes.append(dict)
        return liste_comptes
    except Exception as e:
        print(f"Error: {e}")
        message = "Une erreur s'est produite pendant l'obtention de la liste des comptes."
        return redirect(url_for('error', message=message))

@app.route("/obtenir_trajets")
def obtenir_trajets():
    try:
        user_id = session['user_id']
        data = Database.get_db().obtenir_trajets(user_id)
        liste_trajets = []
        for d in data :
            dict = {'date': str(d[0]), 'lat': d[1], 'lng': d[2], 'nav': d[3], 'dataTrajets': d[4], 'rayon' : d[5], 'poly': d[6], 'travelAd': d[7], 'liste': d[8], 'weather': d[9], 'id' : str(d[10])}
            liste_trajets.append(dict)
        return liste_trajets
    except Exception as e:
        print(f"Error: {e}")
        message = "Une erreur s'est produite pendant l'obtention de la liste des trajets."
        return redirect(url_for('error', message=message))


##############################################################################
#                                                                            #
#                    SECTION POUR TESTER DES TRUCS                           #
#                                                                            #
##############################################################################

@app.route('/get_liste_villes', methods=['POST'])
def get_liste_villes():
    data = request.json
    id_pays = data.get('id_pays')
    liste_villes = Database.get_db().obtenir_liste_villes(id_pays)
    villes_dict = []
    for ville in liste_villes:
            name = ville[0]
            latitude = ville[1]
            longitude = ville[2]
            coordonnees = str(latitude) + ";" + str(longitude)
            current_dict = {"name" : name, "coordonnees" : coordonnees}
            villes_dict.append(current_dict)
    return jsonify(villes_dict)

##############################################################################
#                                                                            #
#                    NE PAS SUPPRIMER EN DESSOUS                             #
#                                                                            #
##############################################################################

# Debug
if __name__ == '__main__':
    app.run(debug = True)
