import json
import sqlite3
from flask import g

class Database():


    # Initie la connexion
    def __init__(self):
        self.connection = None


    # Ouvre la connexion
    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('db/database.db')
        return self.connection


    # Ferme la connexion
    def deconnection(self):
        if self.connection is not None:
            self.connection.close()


    # Obtenir la base de données
    def get_db():
            database = getattr(g, "_database", None)
            if database is None:
                g._database = Database()
            return g._database


    # Insère un nouveau compte utilisateur dans la base de données
    def create_user(self, firstname, name, birthdate, email, salt, hash) :
        try:
            connection = self.get_connection()
            connection.execute("""INSERT INTO users (firstname, name, birthdate, email,
                    salt, hash) VALUES (?, ?, ?, ?, ?, ?)""",
                    (firstname, name, birthdate, email,
                    salt, hash))
            connection.commit()
        except sqlite3.Error as e:
            raise Exception(f"Echec de la creation du compte: {e}")
        finally:
            connection.close()



    # Retourne les informations de l'utilisateur correspondant à l'adresse courriel passée
    # en paramètre, si l'adresse n'existe pas, retourne None
    def get_user(self, email) :
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        
        if user_row is None:
            return None

        user = {
            'id': user_row[0],
            'firstname': user_row[1],
            'name': user_row[2],
            'birthdate': user_row[3],
            'email': user_row[4],
            'salt': user_row[5],
            'hash': user_row[6],
            'confirmed': user_row[7],
            'admin' : user_row[8]
        }
        return user
    
     # Met à jour l'email confirmé
    def confirm_user_email(self, email):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET confirmed = TRUE WHERE email = ?", (email,))
        connection.commit()
        cursor.close()
        connection.close()

    # Met un mot de passe à jour
    def update_password(self, email, new_password, new_salt):
        connection = self.get_connection()
        cursor = connection.cursor()

        # Update the password hash and salt
        query = "UPDATE users SET hash = ?, salt = ? WHERE email = ?"
        cursor.execute(query, (new_password, new_salt, email))
        print(f"Le mot de passe pour {email} a été mis à jour avec le hash: {new_password} et le sel: {new_salt}")

        # Commit changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()



    # Supprime les informations de l'utilisateur correspondant à l'adresse courriel passée
    # en paramètre.
    def delete_user(self, email):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        succes = cursor.fetchall()
        connection.commit()
        connection.close()
        if succes:
            return True
        else:
            return False

    # Ajoute un commentaire dans la base de données
    def ajouter_commentaire(self, est_satisfait, commentaire, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO commentaires (date, est_satisfait, commentaire, user_id) VALUES (datetime('now'),?,?,?)""", (int(est_satisfait), commentaire, user_id))  
            connection.commit()
            connection.close()
            return True
        except sqlite3.Error as e:
            print(f"UNe erreur s'est produite lors de l'ajout du commentaire: {e}")
            connection.close()
            return False

    # Retourne la liste de tous les pays
    def obtenir_liste_pays(self):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM countries")
        liste_pays = cursor.fetchall()
        connection.close()
        return liste_pays
    
    # Retourne la liste de toutes les villes
    def obtenir_liste_villes(self, id_pays):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT cities.name, cities.latitude, cities.longitude FROM cities INNER JOIN countries ON cities.country_id = countries.id WHERE countries.id = ? ORDER BY cities.name""", (int(id_pays),))
        liste_villes = cursor.fetchall()
        connection.close()
        return liste_villes
    
    # Retourne la liste de tous les commentaires de tous les utilisateurs
    def obtenir_liste_commentaires(self) :
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT commentaire_id, date, est_satisfait, commentaire, user_id FROM commentaires""")
            liste_commentaires = cursor.fetchall()
            return liste_commentaires
        except sqlite3.Error as e:
            print(f"Une erreur s'est produite lors de l'obtention de la liste de commentaires: {e}")
            connection.close()
            return False
    
    # Retourne la liste de tous les comptes de tous les utilisateurs
    def obtenir_liste_comptes(self) :
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT id, firstname, name, email FROM users where admin != 1 """)
            liste_comptes = cursor.fetchall()
            return liste_comptes
        except sqlite3.Error as e:
            print(f"Une erreur s'est produite lors de l'obtention de la liste de commentaires: {e}")
            connection.close()
            return False
        
    def sauvegarder_trajet(self, lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather, user_id) :
        connection = self.get_connection()
        weather_dict = json.dumps(weather)
        try:
            cursor = connection.cursor()
            cursor.execute("""INSERT INTO trajets (date, lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather, user_id) VALUES
                    (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ? ,? )""", (lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather_dict, user_id))
            connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"UNe erreur s'est produite lors de la sauvegarde du trajet: {e}")
            connection.close()
            return False

    def obtenir_trajets(self, user_id) :
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT date, lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather, id FROM trajets where user_id = ? ORDER BY date""", (user_id,))
            data = cursor.fetchall()
            connection.commit()
            return data
        except sqlite3.Error as e:
            print(f"Une erreur s'est produite lors de l'obtention de la liste de trajets: {e}")
            connection.close()
            return False

    def obtenir_trajets_par_id(self, id) :
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT date, lat, lng, nav, dataTrajets, rayon, poly, travelAd, liste, weather FROM trajets where id = ?""", (id,))
        data = cursor.fetchone()
        connection.commit()
        return data
