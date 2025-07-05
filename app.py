from flask import Flask, render_template, request, session, redirect, url_for
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "una_clave_secreta_super_segura"
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("title")
    movies = []
    error = None
    history = session.get("history", [])

    if query:
        session["last_search_url"] = request.url  # Guarda la búsqueda completa
        if query not in history:
            history.insert(0, query)
            session["history"] = history[:10]

        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("Response") == "True":
                for item in data.get("Search", []):
                    movies.append({
                        "title": item.get("Title"),
                        "year": item.get("Year"),
                        "imdb_id": item.get("imdbID"),
                        "poster": item.get("Poster") if item.get("Poster") != "N/A" else None
                    })
            else:
                error = data.get("Error", "No results found.")
        except requests.exceptions.RequestException:
            error = "Error connecting to the movie service."

    return render_template("index.html", movies=movies, error=error, history=history)

@app.route("/search", methods=["POST"])
def search():
    title = request.form.get("title")
    if title:
        return redirect(url_for("index", title=title))
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear_history():
    session.pop("history", None)
    return redirect(url_for("index"))

@app.route("/movie/<imdb_id>")
def movie_detail(imdb_id):
    movie = None
    error = None
    back_url = session.get("last_search_url", url_for("index"))

    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=full"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("Response") == "True":
            movie = {
                "title": data.get("Title"),
                "year": data.get("Year"),
                "plot": data.get("Plot"),
                "poster": data.get("Poster") if data.get("Poster") != "N/A" else None,
                "genre": data.get("Genre"),
                "director": data.get("Director"),
                "actors": data.get("Actors"),
                "imdb_id": data.get("imdbID")
            }
        else:
            error = data.get("Error", "Movie not found.")
    except requests.exceptions.RequestException:
        error = "Error connecting to the movie service."

    return render_template("movie_detail.html", movie=movie, error=error, back_url=back_url)

@app.route("/favorite/<imdb_id>", methods=["POST"])
def add_to_favorites(imdb_id):
    favorites = session.get("favorites", [])
    if imdb_id not in favorites:
        favorites.append(imdb_id)
        session["favorites"] = favorites
    return redirect(url_for("movie_detail", imdb_id=imdb_id))

@app.route("/favorites")
def view_favorites():
    favorites = session.get("favorites", [])
    movie_data = []
    for imdb_id in favorites:
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("Response") == "True":
                movie_data.append({
                    "title": data.get("Title"),
                    "year": data.get("Year"),
                    "imdb_id": data.get("imdbID"),
                    "poster": data.get("Poster") if data.get("Poster") != "N/A" else None
                })
        except requests.exceptions.RequestException:
            continue
    return render_template("favorites.html", movies=movie_data)

@app.route("/unfavorite/<imdb_id>", methods=["POST"])
def remove_from_favorites(imdb_id):
    favorites = session.get("favorites", [])
    if imdb_id in favorites:
        favorites.remove(imdb_id)
        session["favorites"] = favorites
    return redirect(url_for("view_favorites"))

if __name__ == "__main__":
    app.run(debug=True)
