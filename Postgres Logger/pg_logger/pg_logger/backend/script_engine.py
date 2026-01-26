import asyncpg
import os

class ScriptEngine:
    """
    Backend engine for Granular Script Generator.
    Handles object discovery and invoking the in-database generation function.
    """
    
    @staticmethod
    async def get_database_objects(pool: asyncpg.Pool) -> dict:
        """
        Fetch all available non-system database objects.
        Returns a dict categorized by type: tables, views, functions.
        """
        query_tables = """
            SELECT n.nspname || '.' || c.relname as name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'r' 
            AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 1;
        """
        
        query_views = """
            SELECT n.nspname || '.' || c.relname as name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'v' 
            AND n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 1;
        """
        
        query_funcs = """
            SELECT n.nspname || '.' || p.proname as name
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY 1;
        """
        
        async with pool.acquire() as conn:
            tables = [r['name'] for r in await conn.fetch(query_tables)]
            views = [r['name'] for r in await conn.fetch(query_views)]
            functions = [r['name'] for r in await conn.fetch(query_funcs)]
            
        return {
            "tables": tables,
            "views": views,
            "functions": functions
        }

    @staticmethod
    async def check_engine_initialized(pool: asyncpg.Pool) -> bool:
        """Check if the generate_deployment_scripts function exists."""
        query = """
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = 'generate_deployment_scripts'
            );
        """
        async with pool.acquire() as conn:
            return await conn.fetchval(query)

    @staticmethod
    async def initialize_engine(pool: asyncpg.Pool) -> None:
        """Injects the PL/pgSQL function into the database."""
        # Read the SQL template relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_path = os.path.join(current_dir, "ddl_template.sql")
        
        with open(sql_path, "r") as f:
            sql_content = f.read()
            
        async with pool.acquire() as conn:
            await conn.execute(sql_content)

    @staticmethod
    async def generate_script(pool: asyncpg.Pool, selected_objects: list[str]) -> str:
        """Call the DB function to generate the script."""
        if not selected_objects:
            return "-- No objects selected."
            
        async with pool.acquire() as conn:
            # Postgres arrays are passed as lists in asyncpg
            return await conn.fetchval(
                "SELECT generate_deployment_scripts($1)", 
                selected_objects
            )
