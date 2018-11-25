drop table if exists family;
drop table if exists genus;
drop table if exists species;

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


.mode tabs
.import tables/family.tsv family
.import tables/genus.tsv genus
.import tables/species.tsv species
