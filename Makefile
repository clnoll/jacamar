DB_PATH:=jacamar.sqlite


tables:
	python bin/create_tables.py input/checklist.tsv


db: tables
	sqlite3 --bail $(DB_PATH) < bin/load_tables.sql


db-shell: db
	rlwrap sqlite3 $(DB_PATH)
