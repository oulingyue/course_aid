-- adding sorting procedure for search bar for documentation 

CREATE OR REPLACE FUNCTION search_prof_by_name(name_input TEXT)
RETURNS TABLE (
    first_name TEXT,
    last_name TEXT,
    avg_rating NUMERIC
) AS $$
	BEGIN
		RETURN QUERY
		with avg_prof as 
		(
		select 
		i.first_name, 
		i.last_name, 
		avg(COALESCE(rating, 0)) as avg_rating
		from review r 
		right outer join instructors i 
		on (r.instructor_last = i.last_name) and 
		(r.instructor_first = i.first_name)
		group by i.first_name,i.last_name
		order by avg_rating DESC
		)
		SELECT *
		FROM avg_prof
		WHERE LOWER(CONCAT(first_name, ' ', last_name)) LIKE CONCAT('%', LOWER(name_input), '%');
	
	END;
$$ LANGUAGE plpgsql;