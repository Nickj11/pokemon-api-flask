from app import app
from flask import render_template, request, redirect, url_for, flash
from .forms import UserCreationForm, PokemonSearchForm, LoginForm, CatchPokemon
from .models import User, Pokemon, Catch, databaseCommit
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
import requests as r
import random

@app.route('/signup', methods=["GET", "POST"])
def signUpPage():
    form = UserCreationForm()
    if request.method == "POST":
        if form.validate():
            username = form.username.data
            name = form.name.data
            email = form.email.data
            password = form.password.data

            user = User(username, name, email, password)

            user.saveToDB()

            return redirect(url_for('FindPokemon'))

    return render_template('signup.html', form = form)


@app.route('/', methods=['GET', 'POST'])
def loginPage():
    form = LoginForm()

    if request.method == "POST":
        if form.validate():
            username = form.username.data
            password = form.password.data

            user = User.query.filter_by(username=username).first()
            if user: 
                if check_password_hash(user.password, password):
                    login_user(user)
                else:
                    flash('WRONG PASSWORD', category='warning')
            else:
                flash('User does not exist', category='warning')
            
        return redirect(url_for('myProfile'))


    return render_template('login.html', form = form)

@app.route('/logout', methods=["GET"])
def logOutRoute():
    form = logout_user()

    return redirect(url_for('findpokemon'))

@app.route('/pokemon/<int:user_id>', methods=["GET", "POST"])
@login_required
def otherUser(user_id):

    other_user = User.query.get(user_id)
    pokemon = Pokemon.query.filter_by(user_id = user_id)
    users=User.query.all()


    return render_template('multiuser.html', pokemon = pokemon, users = users, other_user = other_user)

@app.route('/pokemon', methods=['GET', 'POST'])
def FindPokemon():
    poke = PokemonSearchForm()
    if request.method == "POST":
        url = f'https://pokeapi.co/api/v2/pokemon/{poke.choose.data}'
        response = r.get(url)
        if response.ok:
            my_dict = response.json()
            pokemon_dict = {}
            pokemon_dict["Name"] = my_dict["name"]
            pokemon_dict["Ability"] = my_dict["abilities"][0]["ability"]["name"]
            pokemon_dict["Base xp"] = my_dict["base_experience"]
            pokemon_dict["Base attack"] = my_dict["stats"][1]["base_stat"]
            pokemon_dict["Base hp"] = my_dict["stats"][0]["base_stat"]
            pokemon_dict["Base d"] = my_dict["stats"][2]["base_stat"]
            pokemon_dict["Front Shiny"] = my_dict["sprites"]["front_shiny"]

        else:
            flash("The pokemon you're looking for does not exist.", category='warning')
            return redirect(url_for('FindPokemon'))

        return render_template('index.html', poke = poke, pokemon_dict = pokemon_dict)
    
    return render_template('index.html', poke = poke)


@app.route('/my_pokemon', methods=["GET"])
@login_required
def MyPokemon():

    pokemon = Pokemon.query.all()
    my_pokemon = current_user.pokemon

    users=User.query.all()

    return render_template('my_pokemon.html', pokemon = pokemon, my_pokemon = my_pokemon, users=users)

@app.route('/my_profile', methods=["GET", "POST"])
@login_required
def MyProfile():

    pokemon = Pokemon.query.all()
    my_pokemon = current_user.pokemon

    users=User.query.all()

    return render_template('my_profile.html', pokemon = pokemon, my_pokemon = my_pokemon, users=users)




@app.route('/catch', methods=['GET', 'POST'])
@login_required
def catchPokemon():
    catch = CatchPokemon()
    if request.method == "POST":
        url = f'https://pokeapi.co/api/v2/pokemon/{catch.choose.data}'
        response = r.get(url)
        if response.ok:
            my_dict = response.json()
            pokemon_dict = {}
            pokemon_dict["Name"] = my_dict["name"]
            pokemon_dict["Front Shiny"] = my_dict["sprites"]["front_shiny"]

            id = my_dict["id"]
            pokename = pokemon_dict["Name"]
            base_hp = my_dict["stats"][0]["base_stat"]
            base_xp = my_dict["base_experience"]
            base_atk = my_dict["stats"][1]["base_stat"]
            base_def = my_dict["stats"][2]["base_stat"]
            img = pokemon_dict["Front Shiny"]

            caught = Pokemon.query.all()
            caught_set = set()
            my_pokemon = Pokemon.query.filter_by(user_id = current_user.id)
            my_pokemon_set = set()
            for name in caught:
                caught_set.add(name.id)
            for poke in my_pokemon:
                my_pokemon_set.add(poke.id)
            if id not in caught_set:
                if len(my_pokemon_set) < 5:
                    pokemon = Pokemon(id, current_user.id, pokename, img, base_xp, base_hp, base_atk, base_def)

                    pokemon.saveToDB()

                    flash(f"{pokename.title()} is on  your team!", category='success')

                else: 
                    flash(f"five pokemon at a time.  To catch {pokename.title()}, please release one pokemon.", category='warning')

            else:
                flash(f"{pokename.title()} has been caught.", category='warning')


        else:
            flash("The pokemon you're looking for does not exist.", category='warning')
            return redirect(url_for('catchPokemon'))

        return render_template('catch.html', pokemon_dict = pokemon_dict, pokename = pokename, id = id, catch=catch, img=img, base_hp=base_hp, base_xp=base_xp, base_def=base_def, base_atk=base_atk)
    
    return render_template('catch.html', catch=catch)

@app.route('/remove/<int:pokemon_id>', methods=["GET", "POST"])
@login_required
def removePoke(pokemon_id):
    
    poke = Pokemon.query.filter_by(id=pokemon_id).filter_by(user_id = current_user.id).first()

    if current_user.id == poke.author.id:
        poke.removeFromDB()
        flash(f"{poke.pokename} removed from your team.", category='warning')
        return redirect(url_for('MyProfile'))

    else:
        flash("Nice Try.", category='warning')
        return redirect(url_for('MyProfile'))





@app.route('/battle/<int:user_id>', methods=["GET", "POST"])
@login_required
def battleUser(user_id):

    other_user = User.query.get(user_id)
    my_pokemon = current_user.pokemon
    opp = other_user.pokemon
    users=User.query.all()


    return render_template('battle.html', my_pokemon = my_pokemon, other_user = other_user, users = users, opp=opp)

@app.route('/results/<int:user_id>', methods=["GET", "POST"])
@login_required
def score(user_id):

    other_user = User.query.get(user_id)
    my_pokemon = current_user.pokemon
    opp = other_user.pokemon
    users=User.query.all()

    my_pokemon_list = []
    other_pokemon_list = []

    for poke in my_pokemon:
        my_pokemon_list.append(poke)

    for poke in other_pokemon_list:
        other_pokemon_list.append(poke)

    i = 0
    my_pokemon_wins = 0
    opp_wins = 0

    results = []
    
    if len(my_pokemon) > len(opp):
        while i < len(opp):
            my_attack = my_pokemon[i].base_atk
            my_defense = my_pokemon[i].base_def
            my_health = my_pokemon[i].base_hp
            opp_attack = opp[i].base_atk
            opp_defense = opp[i].base_def
            opp_health = opp[i].base_hp
            while True:
                attacker = ['my_pokemon', 'opponent']
                x = random.choice(attacker)
                print(x)
                if x == 'my_pokemon':
                    opp_defense -= my_attack
                    if opp_defense < 0:
                        opp_health += opp_defense
                    if opp_health < 0:
                        my_pokemon_wins += 1
                        results.append(current_user)
                        break
                else:
                    my_defense -= opp_attack
                    if my_defense < 0:
                        my_health += my_defense
                    if my_health < 0:
                        opp_wins += 1
                        results.append(other_user)
                        break
            print(my_pokemon_wins)
            print(opp_wins)
            print(results)
            
            i += 1
            continue
    else:
        while i < len(my_pokemon):
            my_attack = my_pokemon[i].base_atk
            my_defense = my_pokemon[i].base_def
            my_health = my_pokemon[i].base_hp
            opp_attack = opp[i].base_atk
            opp_defense = opp[i].base_def
            opp_health = opp[i].base_hp
            while True:
                attacker = ['my_pokemon', 'opponent']
                x = random.choice(attacker)
                print(x)
                if x == 'my_pokemon':
                    opp_defense -= my_attack
                    if opp_defense < 0:
                        opp_health += opp_defense
                    if opp_health < 0:
                        my_pokemon_wins += 1
                        results.append(current_user)
                        break
                else:
                    my_defense -= opp_attack
                    if my_defense < 0:
                        my_health += my_defense
                    if my_health < 0:
                        opp_wins += 1
                        results.append(other_user)
                        break
            print(my_pokemon_wins)
            print(opp_wins)
            print(results)
            
            i += 1
            continue
    

    results_len = len(results)

    if my_pokemon_wins > opp_wins:
        current_user.wins += 1
    else:
        other_user.wins += 1
    

    databaseCommit()

    return render_template('results.html', my_pokemon = my_pokemon, other_user = other_user, users = users, opp=opp, results = results, results_len = results_len, my_pokemon_wins=my_pokemon_wins, opp_wins=opp_wins)





