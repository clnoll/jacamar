import os


def get_db_connection():
    pass

DB = get_db_connection()

n_options = 9

base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir, os.pardir))
working_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), os.pardir))
recording_dir = os.path.join(base_dir, 'recordings')
template_dir = os.path.join(working_dir, 'templates')
