from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv("../environment_variables/.env")
API_KEY = os.getenv('MOVIE_DB_API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Bootstrap(app)


# ***** CREATE TABLE ****
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


# db.create_all()
#
#
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()

# ***** CREATE FORM *******
class RateMovieForm(FlaskForm):
    rating = StringField(label='Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField(label='Done')


class AddMovie(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    # gives in ascending order
    movie_list = Movie.query.order_by(Movie.rating).all()[::-1]
    new_list = []
    for movie in movie_list:
        movie.ranking = movie_list.index(movie) + 1
        db.session.commit()
        new_list.append(movie)
    return render_template("index.html", movies=new_list[::-1])


@app.route('/edit<int:movie_id>', methods=['POST', 'GET'])
def edit(movie_id):
    form = RateMovieForm()
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie_to_update)


@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        parameters = {
            "api_key": API_KEY,
            "query": form.title.data,
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=parameters)
        response.raise_for_status()
        data = response.json()['results']
        return render_template('select.html', data=data)
    return render_template('add.html', form=form)


@app.route('/getmovie/<int:movie_id>', methods=['POST', 'GET'])
def getmovie(movie_id):
    parameters = {
        "api_key": API_KEY,
    }
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url=url, params=parameters)
    response.raise_for_status()
    data = response.json()
    new_movie = Movie(
        title=data['original_title'],
        year=data['release_date'].split('-')[0],
        description=data['overview'],
        img_url="https://image.tmdb.org/t/p/original" + data['poster_path']
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
