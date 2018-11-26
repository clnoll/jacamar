from jacamar.app import api
from jacamar.resources import Recording

api.add_route('/recording/{recording_id}', Recording(None))