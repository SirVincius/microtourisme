from flask import current_app
import hashlib
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,SubmitField,  DateTimeField, EmailField, ValidationError, SelectField
from wtforms.validators import InputRequired, DataRequired, Email, EqualTo, Length
from database import Database


# Formulaire de création de compte
class AccountForm(FlaskForm):
    firstName = StringField('Prénom', validators=[InputRequired('Prénom obligatoire')])
    name = StringField('Nom', validators=[InputRequired('Nom obligatoire')])
    birthdate = DateTimeField('Date de naissance', format='%Y-%m-%d', validators=[InputRequired('Date de naissance obligatoire')])
    email = EmailField('Adresse courriel', validators=[InputRequired('Adresse courriel obligatoire'), Email('Adresse courriel invalide')])
    password = PasswordField('Mot de passe', validators=[InputRequired('Mot de passe obligatoire'), Length(8, 20, "Le mot de passe doit contenir entre 8 et 20 caractères")])
    passwordConfirmation = PasswordField('Confirmation du mot de passe', validators=[InputRequired('Confirmation du mot de passe obligatoire'),
                                                                                     EqualTo('password', message='Les mots de passe doivent être identiques')])

    def validate_email(form, field):
        user = Database.get_db().get_user(field.data)
        if user is not None:
            raise ValidationError("Veuillez utiliser une adresse courriel différente")


# Formulaire de connexion
class LoginForm(FlaskForm):
    email = EmailField('Adresse courriel', validators=[InputRequired('Adresse courriel obligatoire'),  Email('Adresse courriel invalide')])
    password = PasswordField('Mot de passe', validators=[InputRequired('Mot de passe obligatoire')])

    def validate_password(self, password):
        email = self.email.data
        user = Database.get_db().get_user(email)  
        if user is None:
            raise ValidationError('Identifiant ou mot de passe invalide')
               
        salt = user['salt']
        hashed_password = hashlib.sha512(str(self.password.data + salt).encode("utf-8")).hexdigest()
        if hashed_password != user['hash']:
            raise ValidationError('Identifiant ou mot de passe invalide')

#formulaire de recuperation de mot de passe
class ResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


# Formulaire de génération d'itinéraire
class GenerationForm(FlaskForm):
    type_of_attraction = [('None','-Select an attraction-'), ('tourist_attraction','Attraction touristique'),
                          ('bar', 'Bar'), ('night_club', 'Boîte de nuit'), ('cafe', 'Café'),
                          ('casino', 'Casino'), ('shopping_mall', 'Centre d\'achat'),('library', 'Librairie'),
                          ('liquor_store', 'Magasin d\'alcool'), ('mosque', 'Mosquée'),
                          ('museum', 'Musée'), ('park', 'Parc'), ('amusement_park', 'Parc d\'attraction'),
                          ('restaurant','Restaurant'), ('spa', 'Spa'), ('stadium', 'Stade'), ('zoo', 'Zoo')]
    
    # Populate countries_choices using obtenir_liste_pays() within the context
    @staticmethod
    def populate_countries_choices():
        with current_app.app_context():
            countries_choices = [('None', 'Selectionnez un pays')] + Database.get_db().obtenir_liste_pays()
        return countries_choices
    
    rayon_ranges = [(250, '250m'), (500, '500m'), (1000, '1km'), (2000, '2km'), (5000, '5km'), (10000, '10km'), (25000, '25km')]
    coordonnees_choices = [('1', 'Fixe_Test'), ('2', 'Position actuelle'), ('3', 'Ville')]
    Optimisation_choices = [('1', 'Hasard'), ('2', 'Mieux Coté'), ('3', 'Plus près'), ('4', 'Moins dispendieux'), ('5', 'Plus dispendieux')]
    Deplacement_types = [('DRIVE', 'Automobile'), ('WALK','Piéton'), ('TRANSIT', 'Transport en commun')]
    
    attraction1 = SelectField('Catégorie 1', choices=type_of_attraction, validators=[InputRequired('Veuillez entrer au moins 1 lieu')])
    attraction2 = SelectField('Catégorie 2', choices=type_of_attraction)
    attraction3 = SelectField('Catégorie 3', choices=type_of_attraction)
    attraction4 = SelectField('Catégorie 4', choices=type_of_attraction)
    attraction5 = SelectField('Catégorie 5', choices=type_of_attraction)
    attraction6 = SelectField('Catégorie 6', choices=type_of_attraction)
    rayon = SelectField('Rayon', choices=rayon_ranges)
    coordonnees = SelectField('Coordonnées', choices=coordonnees_choices)
    pays = SelectField('Pays', choices=populate_countries_choices, render_kw={"disabled": True})  # Use function reference here
    ville = SelectField('Villes', choices=[('None', 'Selectionnez une ville')],  render_kw={"disabled": True})
    Optimisation = SelectField('Optimisation', choices=Optimisation_choices)
    Deplacement = SelectField('Deplacement', choices=Deplacement_types)
    

# formulaire liste selections
class Selection(FlaskForm):
    sel = list()