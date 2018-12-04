import os
import sqlite3
from collections import defaultdict

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
        self.connection.row_factory = sqlite3.Row

    def execute(self, query):
        return self.connection.cursor().execute(query)


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

    def _group_recording_by_species(self, query_results):
        grouped_results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for el in query_results:
            family_key = '{family_english_name} ({family}) {weight}g'.format(**el)
            species = grouped_results[family_key][el['genus']][el['species']]
            recording = (el['type'], el['id'])
            if 'recordings' in species:
                species['recordings'] += [recording]
            else:
                species['recordings'] = [recording]
            species['image_url'] = el['url']
            species['english_name'] = el['english_name']
            species['name'] = '%s %s' % (el['genus'], el['species'])
        return grouped_results

    def on_get(self, request, response, recording_id=None):
        error = None

        if recording_id is None:
            query = f"""
            select family.name as family, family.english_name as family_english_name, family.weight,
                   genus.name as genus,
                   species.name as species, species.english_name as english_name,
                   recording.id, recording.type,
                   image.url
            from species
            inner join image on species.id = image.species_id
            inner join recording on recording.species_id = species.id
            inner join genus on species.genus_id = genus.id
            inner join family on genus.family_id = family.id
            order by family.weight, genus.name, species.name
            """
            query_results = self.db.connection.cursor().execute(query).fetchall()
            template_path = os.path.join(settings.template_dir, 'recordings.html')
            response.content_type = falcon.MEDIA_HTML
            response.body = load_template(template_path).render(
                results=self._group_recording_by_species(query_results))
        else:
            query = f"""
            select path from recording where id = {recording_id}
            """
            [recording_path] = self.db.connection.cursor().execute(query).fetchone()
            with open(recording_path, 'rb') as fp:
                response.body = fp.read()
            response.content_type = "audio/mpeg"

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


class RecordingQuiz(BaseResource):

    def get_families_with_songs(self):
        family_query = """
        select distinct family.id, family.name, family.english_name, family.weight
        from recording join species on species.id = recording.species_id
        join genus on genus.id = species.genus_id
        join family on family.id = genus.family_id
        where recording.type like '%song%'
        and not family.name in ('Hirundinidae')
        order by family.weight
        """
        families = self.db.connection.cursor().execute(family_query).fetchall()

        image_query = """
        select family.name, image.url
        from image
        join species on species.id = image.species_id
        join genus on genus.id = species.genus_id
        join family on family.id = genus.family_id
        order by random()
        """
        images = self.db.connection.cursor().execute(image_query).fetchall()
        family2image_urls = defaultdict(list)
        for family, url in images:
            family2image_urls[family].append(url)

        families = list(map(dict, families))

        for family in families:
            family['image_urls'] = family2image_urls[family['name']]

        return families

    def _on_get_recording_quiz(self, recording, response):
        template_path = os.path.join(settings.template_dir, 'recording_quiz.html')
        families = self.get_families_with_songs()
        response.body = (load_template(template_path)
                         .render(recording=recording,
                                 families=families))
        response.status = falcon.HTTP_200
        response.content_type = falcon.MEDIA_HTML

    def on_get(self, request, response):
        # TODO: species.id is not used
        recording_query = """
        select recording.id, species.id as species_id, species.english_name, family.id as family_id from recording
        join species on recording.species_id = species.id
        inner join genus on genus.id = species.genus_id
        inner join family on family.id = genus.family_id
        where recording.id in (
          select recording.id from recording
          where type like '%song%'
          order by random()
          limit 1
        )
        and not family.name in ('Hirundinidae')
        """
        recording = self.db.connection.cursor().execute(recording_query).fetchone()
        self._on_get_recording_quiz(recording, response)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red(f"Truth: {dict(recording)}"))


    def on_post(self, request, response):
        form_data = parse_form_data(request)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red(f'form data: {form_data}'))

        query = f"""
        select family.id from recording
        inner join species on species.id = recording.species_id
        inner join genus on genus.id = species.genus_id
        inner join family on family.id = genus.family_id
        where recording.id = {form_data['recording_id']}
        """
        [species_family_id] = self.db.execute(query).fetchone()
        species_family_id = int(species_family_id)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red('recording %s is family %s' % (form_data['recording_id'], species_family_id)))

        if form_data['family_id'] == species_family_id:
            response.body = 'Success! On to genus and species...'
            response.status = falcon.HTTP_200
            response.content_type = falcon.MEDIA_HTML
        else:
            recording = {'id': form_data['recording_id']}
            self._on_get_recording_quiz(recording, response)


class ImageQuiz(BaseResource):

    def _group_recording_by_species(self, query_results):
        grouped_results = defaultdict(dict)
        for el in query_results:
            key = '{english_name} ({genus_name} {species_name}) {weight}g'.format(**el)
            if 'recording_ids' in grouped_results[key]:
                grouped_results[key]['recording_ids'].append(el['recording_id'])
            else:
                grouped_results[key]['recording_ids'] = [el['recording_id']]
            grouped_results[key]['species_id'] = el['species_id']
        return grouped_results

    def get_species_with_songs(self, family_id):
        species_query = f"""
        select distinct species.id as species_id, genus.name as genus_name, species.name as species_name, species.english_name, family.weight, recording.id as recording_id
        from recording join species on species.id = recording.species_id
        join genus on genus.id = species.genus_id
        join family on family.id = genus.family_id
        where recording.type like '%song%'
        and family.id = {family_id}
        and not family.name in ('Hirundinidae')
        order by family.weight
        """
        results = self.db.connection.cursor().execute(species_query).fetchall()
        return self._group_recording_by_species(results)

    def _on_get_image_quiz(self, image, response):
        template_path = os.path.join(settings.template_dir, 'image_quiz.html')
        species = self.get_species_with_songs(image['family_id'])
        response.body = (load_template(template_path)
                         .render(image=image,
                                 species=species))
        response.status = falcon.HTTP_200
        response.content_type = falcon.MEDIA_HTML

    def on_get(self, request, response):
        image_query = """
        select image.id, image.url, species.english_name, family.id as family_id, species.id as species_id from image
        join species on image.species_id = species.id
        inner join genus on genus.id = species.genus_id
        inner join family on family.id = genus.family_id
        where image.id in (
          select image.id from image
          join recording on recording.species_id = image.species_id
          where type like '%song%'
          order by random()
          limit 1
        )
        and not family.name in ('Hirundinidae')
        """
        image = self.db.connection.cursor().execute(image_query).fetchone()
        self._on_get_image_quiz(image, response)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red(f"Truth: {dict(image)}"))

    def on_post(self, request, response):
        form_data = parse_form_data(request)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red(f'form data: {form_data}'))
        image_id = form_data['image_id']
        guessed_species_id = form_data['species_id']

        query = f"""
        select species.id from image
        inner join species on species.id = image.species_id
        inner join genus on genus.id = species.genus_id
        inner join family on family.id = genus.family_id
        where image.id = {image_id}
        """
        [actual_species_id] = self.db.execute(query).fetchone()
        actual_species_id = int(actual_species_id)

        from clint.textui import colored; red = lambda s: colored.red(s, bold=True)
        print(red('image %s is species %s' % (form_data['species_id'], actual_species_id)))

        if guessed_species_id == actual_species_id:
            response.body = 'Success!'
            response.status = falcon.HTTP_200
            response.content_type = falcon.MEDIA_HTML
        else:
            image_query = f"""
                select image.id, image.url, species.english_name, family.id as family_id, species.id as species_id from image
                join species on image.species_id = species.id
                inner join genus on genus.id = species.genus_id
                inner join family on family.id = genus.family_id
                where image.id = {image_id}
            """
            image = self.db.connection.cursor().execute(image_query).fetchone()
            self._on_get_image_quiz(image, response)


def parse_form_data(request):
    SEP = '--'
    raw_data = request.stream.read().decode('utf-8')
    _, raw_data = raw_data.split('=', 1)
    raw_data = raw_data.split(SEP)
    assert len(raw_data) % 2 == 0
    raw_data = iter(raw_data)
    data = {}
    while True:
        try:
            key = next(raw_data)
        except StopIteration:
            return data
        else:
            value = next(raw_data)
            try:
                value = int(value)
            except ValueError:
                pass
            assert key not in data
            data[key] = value
