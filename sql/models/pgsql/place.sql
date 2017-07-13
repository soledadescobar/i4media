create table place (
	id serial primary key,
	attributes text[][],
	country character(50),
	country_code character(3),
	full_name character(100),
	id_places character(250),
	name character(250),
	place_type character(50),
	url character(250)
);
