create table bounding_box (
	id integer auto_increment primary key,
	id_place bigint,
	coordinates text,
	type varchar(50)
);


