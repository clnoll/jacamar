import falcon

from jacamar.api import image
from jacamar.api import image_quiz
from jacamar.api import recording
from jacamar.api import recording_quiz


api = application = falcon.API()

api.add_route('/image-quiz', image_quiz)
api.add_route('/recording-quiz', recording_quiz)

api.add_route('/recordings/{recording_id}', recording)
api.add_route('/recordings', recording)
api.add_route('/images/{family_id}', image)
