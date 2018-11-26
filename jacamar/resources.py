import falcon

from jacamar import settings


class BaseResource(object):

    def __init__(self):
        self.db = settings.DB


class Recording(BaseResource):

    def on_get(self, request, response, recording_id):
        try:
            recording = self.db.get_recording(recording_id)
        except Exception as ex:
            response.context['result'] = 'error'
        else:
            response.context['result'] = recording
            response.status = falcon.HTTP_200


class Classification(BaseResource):

    def __init__(self, classification_level):
        super().__init__()
        self.level = classification_level

    def on_post(self, request, response, recording_id, classification_name):
        try:
            family_id, genus_id, species_id = self.db.get_classification_by_recording(recording_id)
            classification_id = self.db.get_classification_by_name(classification_name, self.level)
        except Exception as ex:
            response.context['result'] = 'error'
        else:
            classifications = {
                'family': family_id,
                'genus': genus_id,
                'species': species_id,
            }
            response.context = ('Correct!' if classifications[self.level] == classification_id
                                else 'Wrong %s!' % self.level)
            response.status = falcon.HTTP_200


class Family(Classification):

    def __init__(self):
        super().__init__(classification_level='family')

    def on_get(self, request, recording_id):
        family_id, genus_id, species_id = self.db.get_classification_by_recording(recording_id)
        other_families = self.db.get_random_families(settings.n_options)


class Genus(Classification):
    def __init__(self):
        super().__init__(classification_level='genus')


class Species(Classification):
    def __init__(self):
        super().__init__(classification_level='species')
