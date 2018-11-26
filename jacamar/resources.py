import os
import sqlite3

import falcon
import jinja2

from jacamar import settings


def load_template(name):
    path = os.path.join(settings.template_dir, name)
    with open(os.path.abspath(path), 'r') as fp:
        return jinja2.Template(fp.read())


class Database:

    def __init__(self):
        self.connection = sqlite3.connect(settings.db_file)

    def get_classification_by_recording(recording_id):
        raise NotImplementedError

    def get_classification_by_name(name, level):
        raise NotImplementedError


class BaseResource(object):

    def __init__(self):
        self.db = Database()


class Image(BaseResource):

    def on_get(self, request, response, family_id=None):
        cursor = self.db.connection.cursor()

        query = f"""
        select family.name, family.english_name from family where family.id = {family_id}
        """
        family_name, family_english_name = cursor.execute(query).fetchone()

        query = f"""
        select genus.name, species.name, species.english_name, image.url from image
        inner join species on image.species_id = species.id
        inner join genus on species.genus_id = genus.id
        inner join family on genus.family_id = family.id
        where family.id={family_id}
        order by genus.name, species.name
        """
        images = list(cursor.execute(query).fetchall())

        template_path = os.path.join(settings.template_dir, 'images.html')
        response.status = falcon.HTTP_200
        response.content_type = falcon.MEDIA_HTML
        response.body = (load_template(template_path)
                         .render(family_name=family_name,
                                 family_english_name=family_english_name,
                                 images=images))


class Recording(BaseResource):

    def on_get(self, request, response, recording_id=None):
        error = None

        if recording_id is None:
            location = os.path.join(settings.template_dir, 'recordings.html')
            recordings = os.listdir(settings.recording_dir)
            results = {el: os.path.join(settings.recording_dir, el) for el in recordings}
        else:
            location = os.path.join(settings.template_dir, 'recording_detail.html')
            try:
                results = self.db.get_recording(recording_id)
            except Exception as ex:
                results = 'Error loading recording %s' % recording_id

        response.status = falcon.HTTP_200
        response.content_type = falcon.MEDIA_HTML
        response.body = load_template(location).render(error=error,
                                                       results=results)


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
            response.location = '...'


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
