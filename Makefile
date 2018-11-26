DB_PATH:=jacamar.sqlite


tables:
	python bin/create_tables.py input/checklist.tsv recordings


db: tables
	sqlite3 --bail $(DB_PATH) < bin/load_tables.sql


db-shell: db
	rlwrap sqlite3 $(DB_PATH)


serve:
	gunicorn jacamar.app


serve-dev:
	gunicorn jacamar.app --reload --workers=1 -t 500
