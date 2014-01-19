import bottle
from bottle import request, abort, static_file
from hashlib import sha1
import json
import random
import os

from random_music_generator import RandomMusicGenerator, output_score

app = bottle.app()

CACHE_FOLDER = '/tmp/random_music_generator'


class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


@app.route('/generate_random_music', method=['POST', 'OPTIONS'])
def generate_random_music():
    music_params = validate_params()
    music_id = '{0:032x}'.format(random.getrandbits(128))
    generate_and_store_random_music(music_params, music_id)
    return {'music_id': music_id}


@app.route('/get_music_as_ly/:music_id', method=['GET', 'OPTIONS'])
def get_music_as_ly(music_id):
    return get_music_as(music_id, 'ly')


@app.route('/get_music_as_pdf/:music_id', method=['GET', 'OPTIONS'])
def get_music_as_pdf(music_id):
    return get_music_as(music_id, 'pdf')


@app.route('/get_music_as_midi/:music_id', method=['GET', 'OPTIONS'])
def get_music_as_midi(music_id):
    return get_music_as(music_id, 'midi')


def get_music_as(music_id, output_type):
    filename = '{0}.{1}'.format(music_id, output_type)
    resp = static_file(filename, root=CACHE_FOLDER)
    resp.headers['Content-Disposition'] = 'attachment; filename=random_music.{0}'.format(output_type)
    return resp


def validate_params():
    try:
        music_params = request.json
        if music_params is None:
            abort(406, 'Content-type must be application/json.')

        if not isinstance(music_params, dict):
            abort(406, 'Request body must be JSON object.')

        return music_params
    except ValueError:
        abort(406, 'Invalid JSON in request body')


def get_music_id(music_params):
    json_content = json.dumps(music_params)
    return sha1(json_content).hexdigest()


def generate_and_store_random_music(music_params, music_id):
    """
    Generates random music based on the given music_params, and
    stores the generated files (ly, pdf and midi) using the music_id
    to generate the filename.

    Example of music_params where each parameter has the default value,
    i.e. the same parameters would have been used if no music_params was present.
    {
        "pitches": [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23],
        "durations": [[1, 10], [0.875, 1], [0.75, 5], [0.5, 30], [0.375, 5], [0.25, 50], [0.125, 50]],
        "measure_size": 4,
        "rest_probability": 0.20,
        "tie_probability": 0.3333,
        "length": 50
    }
    """
    init_params = get_sub_dict(music_params,
                               ['pitches', 'durations', 'measure_size', 'rest_probability', 'tie_probability'])
    random_music_generator = RandomMusicGenerator(**init_params)
    score_params = get_sub_dict(music_params, ['length'])
    score = random_music_generator.generate_random_score(**score_params)
    ly_filepath = os.path.join(CACHE_FOLDER, '{0}.ly'.format(music_id))
    if not os.path.exists(CACHE_FOLDER):
        os.makedirs(CACHE_FOLDER)
    output_score(score, ly_filepath)


def get_sub_dict(orig_dict, keys):
    sub_dict = {}
    for key in keys:
        if key in orig_dict:
            sub_dict[key] = orig_dict[key]
    return sub_dict

app.install(EnableCors())
# app.run(host='localhost', port=8081, reloader=True, debug=True)
