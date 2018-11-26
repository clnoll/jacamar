import falcon

from jacamar.api import image
from jacamar.api import recording


api = application = falcon.API()

api.add_route('/recordings/{recording_id}', recording)
api.add_route('/recordings', recording)
api.add_route('/images/{family_id}', image)
