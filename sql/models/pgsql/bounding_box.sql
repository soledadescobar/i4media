create table bounding_box (
	id serial primary key,
	id_place bigint,
	coordinates text,
	type character(50)
);
