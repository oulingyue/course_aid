-- adding sorting procedure for search bar for documentation 
CREATE OR REPLACE FUNCTION search_prof_by_name(
    name_input TEXT,
        dept_filter TEXT DEFAULT NULL,
        sort_asc BOOLEAN DEFAULT FALSE)
RETURNS TABLE (
    first_name TEXT,
    last_name TEXT,
    avg_rating NUMERIC
) AS $$
	BEGIN
		RETURN QUERY
		with avg_prof AS (
		select 
		    i.first_name, 
		    i.last_name, 
            i_d.department_name,
		    avg(COALESCE(rating, 0)) as avg_rating
		from review r 
		right outer join instructors i 
		    on (r.instructor_last = i.last_name) and 
		    (r.instructor_first = i.first_name)
        left outer join instructor_to_department i_d
            on (i.last_name = i_d.instructor_last) and 
		    (i.first_name = i_d.instructor_first)
		group by i.first_name,i.last_name, i_d.department_name
		order by avg_rating DESC
		)
		SELECT ap.first_name::TEXT, ap.last_name::TEXT, ap.avg_rating
		FROM avg_prof ap
		WHERE LOWER(CONCAT(ap.first_name, ' ', ap.last_name)) LIKE CONCAT('%', LOWER(name_input), '%')AND (dept_filter IS NULL OR ap.department_name = dept_filter)
    ORDER BY 
        CASE WHEN sort_asc THEN ap.avg_rating END ASC,
        CASE WHEN NOT sort_asc THEN ap.avg_rating END DESC;
END;
$$ LANGUAGE plpgsql;;


-- search by course number 
CREATE OR REPLACE FUNCTION search_prof_by_course(
    course_input TEXT,
    dept_filter TEXT DEFAULT NULL,
    sort_asc BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    first_name TEXT,
    last_name TEXT,
    avg_rating NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH avg_prof AS (
        SELECT 
            i.first_name, 
            i.last_name,
            i_d.department_name,
            AVG(COALESCE(r.rating, 0)) AS avg_rating
        FROM instructors i
        LEFT JOIN review r
            ON r.instructor_first = i.first_name
            AND r.instructor_last = i.last_name
        LEFT JOIN instructor_to_department i_d
            on (i.last_name = i_d.instructor_last) and 
		    (i.first_name = i_d.instructor_first)
        GROUP BY i.first_name, i.last_name, i_d.department_name
    )
    SELECT ap.first_name::TEXT, ap.last_name::TEXT, ap.avg_rating
    FROM avg_prof ap
    INNER JOIN course_section cs
        ON ap.first_name = cs.instructor_first
        AND ap.last_name = cs.instructor_last
    WHERE LOWER(cs.course_number) LIKE CONCAT('%', LOWER(course_input), '%')
        AND (dept_filter IS NULL OR ap.department_name = dept_filter)
    ORDER BY 
        CASE WHEN sort_asc THEN ap.avg_rating END ASC,
        CASE WHEN NOT sort_asc THEN ap.avg_rating END DESC;
END;
$$ LANGUAGE plpgsql;