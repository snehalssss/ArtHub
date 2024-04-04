from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Sample art art_shows data
art_shows = [
    {
        'title': 'ART EXHIBITION',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': 'art-gallery-exhibition-vertical-poster-template_23-2149721708.jpg'
    },
    {
        'title': 'THE ART FAIR',
        'description': 'It is the subcontinent\'s most-awaited fair... a treat for collectors and connoisseurs.',
        'image': 'images.jpeg'
    },
    {
        'title': 'DIGITAL ART ',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': '367.jpeg'
    },
    {
        'title': 'INDIA ART_art_show',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': 'india_art.jpeg'
    },
    {
        'title': 'ART art_show - MOUNT VIEW',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': 'images.png'
    },
    {
        'title': 'ART EXHIBITION',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': '820928489dd2f_377490.png_detail.jpg'
    },
    {
        'title': 'LA ART art_show',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': 'LOGO.jpg'
    },
    {
        'title': 'CREATIVEHIVE',
        'description': 'A visual object experience consciously created through an expression of skill or imagination. ',
        'image': 'creativehive.png'
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_art_shows')
def get_art_shows():
    return jsonify({'artShows': art_shows})

if __name__ == "__main__":
    app.run(debug=True)