import sqlite3
import asyncio
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.format_as_xml import format_as_xml
from datetime import date
import re
from dotenv import load_dotenv
load_dotenv()

DB_SCHEMA = '''
        CREATE TABLE Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL UNIQUE,
        address TEXT,
        city TEXT,
        state TEXT,
        postal_code TEXT,
        country TEXT,
        date_of_birth DATE,
        join_date DATE DEFAULT CURRENT_DATE
    );
'''

SQL_EXAMPLES = [
    {
        'request': 'show me records where the country is "USA"',
        'response': "SELECT * FROM Users WHERE country = 'USA'",
    },
    {
        'request': 'show me records with the state "California"',
        'response': "SELECT * FROM Users WHERE state = 'California'",
    },
    {
        'request': 'show me records where the phone number starts with "123"',
        'response': "SELECT * FROM Users WHERE phone_number LIKE '123%'",
    },
    {
        'request': 'add a new user named Alice with email alice@example.com', 
        'response': "INSERT INTO Users (first_name, last_name, email, phone_number) VALUES ('Alice', 'Smith', 'alice@example.com', '9876543210')"
    },
    {
        'request': 'add a new user named Alice with email alice@example.com',
        'response': "INSERT INTO Users (first_name, last_name, email, phone_number) VALUES ('Alice', 'Smith', 'alice@example.com', '9876543210')"
    },
    {
        'request': 'add a new user named Bob with email bob@example.com',
        'response': "INSERT INTO Users (first_name, last_name, email, phone_number) VALUES ('Bob', 'Johnson', 'bob@example.com', '1234567890')"
    },  
    {
        'request': 'add a new user named Charlie with email charlie@example.com',
        'response': "INSERT INTO Users (first_name, last_name, email, phone_number) VALUES ('Charlie', 'Brown', 'charlie@example.com', '2345678901')"
    },
    {
        'request': 'update the email of John to john.doe@example.com', 
        'response': "UPDATE Users SET email = 'john.doe@example.com' WHERE first_name = 'John'"
    },
    {
        'request': 'update the phone number of Alice to 1112223333',
        'response': "UPDATE Users SET phone_number = '1112223333' WHERE first_name = 'Alice' AND last_name = 'Smith'"
    },
    {
        'request': 'update the city of Bob to Los Angeles',
        'response': "UPDATE Users SET city = 'Los Angeles' WHERE first_name = 'Bob' AND last_name = 'Johnson'"
    },
    {
        'request': 'update the postal code of Charlie to 90210',
        'response': "UPDATE Users SET postal_code = '90210' WHERE first_name = 'Charlie' AND last_name = 'Brown'"
    },
    {
        'request': 'delete users where country is India', 
        'response': "DELETE FROM Users WHERE country = 'India'"
    },
    {
        'request': 'delete users where the city is "New York"',
        'response': "DELETE FROM Users WHERE city = 'New York'"
    },
    {
        'request': 'delete users where the country is "Canada"',
        'response': "DELETE FROM Users WHERE country = 'Canada'"
    },
    {
        'request': 'delete users whose join date is older than "2020-01-01"',
        'response': "DELETE FROM Users WHERE join_date < '2020-01-01'"
    },
]

@dataclass
class Deps:
    conn: sqlite3.Connection

agent = Agent(
    'groq:llama-3.1-8b-instant',
    system_prompt=f'''
        You are a SQL assistant for a telecom database. 
        You generate SQL queries based on user requests. 
        The database schema is:

        {DB_SCHEMA}
        Today's date = {date.today()}

        Follow these rules:
        - Use `SELECT` for reading records.
        - Use `INSERT INTO` for adding new records.
        - Use `UPDATE` to modify existing records.
        - Use `DELETE FROM` for removing records.
        - Generate safe, executable SQLite queries.
        
        Examples:
        {SQL_EXAMPLES}
    ''',
    deps_type=Deps,
)

async def main(prompt):
    conn = sqlite3.connect('users.db')
    
    deps = Deps(conn)
    result = await agent.run(prompt, deps=deps)
    raw_query = result.data
    sql_query = re.sub(r"^```sql\s*|\s*```$", "", raw_query).strip()
    print(sql_query)
    
    cursor = conn.cursor()
    cursor.execute(sql_query)
    if re.match(r"^SELECT", sql_query, re.IGNORECASE):
        rows = cursor.fetchall()
        for row in rows:
            return row
    else:
        conn.commit()
        
    conn.close() 

# asyncio.run(main())

