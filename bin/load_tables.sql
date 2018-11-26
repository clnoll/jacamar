drop table if exists family;
drop table if exists genus;
drop table if exists species;
drop table if exists recording;
drop table if exists image;

create table family (
  id integer primary key,
  name text not null,
  english_name text not null
);

create table genus (
  id integer primary key,
  name text not null,
  english_name text,
  family_id integer,
  foreign key (family_id) references family (id)
);

create table species (
  id integer primary key,
  name text not null,
  english_name text not null,
  genus_id integer,
  foreign key (genus_id) references genus (id)
);

create table recording (
  id integer primary key,
  path text not null,
  species_id integer,
  type text not null,
  foreign key (species_id) references species (id)
);

create table image (
  id integer primary key,
  url text not null,
  species_id integer,
  foreign key (species_id) references species (id)
);

.mode tabs
.import tables/family.tsv family
.import tables/genus.tsv genus
.import tables/species.tsv species
.import tables/recording.tsv recording
.import tables/image.tsv image
