CREATE OR REPLACE FUNCTION generate_deployment_scripts(selected_objects TEXT[])
RETURNS TEXT AS $$
DECLARE
    obj_name TEXT;
    schema_name TEXT;
    table_name TEXT;
    ddl_output TEXT := '';
    obj_type TEXT;
    def TEXT;
    rec RECORD;
BEGIN
    ddl_output := '-- Generated Deployment Script' || E'\n' || 
                  '-- Date: ' || NOW()::TEXT || E'\n\n';

    FOREACH obj_name IN ARRAY selected_objects
    LOOP
        -- Split schema.name. Assumes clean input "schema.name"
        schema_name := split_part(obj_name, '.', 1);
        table_name := split_part(obj_name, '.', 2);

        -- Detect object type
        SELECT 
            CASE 
                WHEN c.relkind = 'r' THEN 'TABLE'
                WHEN c.relkind = 'v' THEN 'VIEW'
                WHEN p.prokind = 'f' THEN 'FUNCTION'
                ELSE 'UNKNOWN'
            END INTO obj_type
        FROM pg_catalog.pg_namespace n
        LEFT JOIN pg_catalog.pg_class c ON n.oid = c.relnamespace AND c.relname = table_name
        LEFT JOIN pg_catalog.pg_proc p ON n.oid = p.pronamespace AND p.proname = table_name
        WHERE n.nspname = schema_name;

        IF obj_type = 'TABLE' THEN
            ddl_output := ddl_output || '-- Table: ' || obj_name || E'\n';
            ddl_output := ddl_output || 'CREATE TABLE ' || obj_name || ' (' || E'\n';
            
            -- Get columns
            FOR rec IN 
                SELECT a.attname, format_type(a.atttypid, a.atttypmod) as type
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_attribute a ON a.attrelid = c.oid
                WHERE n.nspname = schema_name AND c.relname = table_name AND a.attnum > 0 AND NOT a.attisdropped
            LOOP
                ddl_output := ddl_output || '    ' || rec.attname || ' ' || rec.type || ',' || E'\n';
            END LOOP;
            
            -- Remove last comma and close
            ddl_output := rtrim(ddl_output, ',' || E'\n') || E'\n' || ');' || E'\n\n';

        ELSIF obj_type = 'VIEW' THEN
            ddl_output := ddl_output || '-- View: ' || obj_name || E'\n';
            ddl_output := ddl_output || 'CREATE OR REPLACE VIEW ' || obj_name || ' AS' || E'\n';
            SELECT pg_get_viewdef(c.oid, true) INTO def
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = schema_name AND c.relname = table_name;
            
            ddl_output := ddl_output || def || E'\n\n';
            
        ELSIF obj_type = 'FUNCTION' THEN
             ddl_output := ddl_output || '-- Function: ' || obj_name || E'\n';
             SELECT pg_get_functiondef(p.oid) INTO def
             FROM pg_proc p
             JOIN pg_namespace n ON n.oid = p.pronamespace
             WHERE n.nspname = schema_name AND p.proname = table_name;
             
             ddl_output := ddl_output || def || E';\n\n';
        END IF;

    END LOOP;

    RETURN ddl_output;
END;
$$ LANGUAGE plpgsql;