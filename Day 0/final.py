from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from datetime import date
import query_generator
import re
from dataclasses import dataclass
import sqlite3
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Deps:
    conn : sqlite3.Connection

web_agent = Agent(
    'groq:gemma2-9b-it',
    system_prompt= "You are Web Search agent who only browse web."
    "You answer questions which are available on Web",
    tools=[duckduckgo_search_tool()]
)

db_agent = Agent(
    'groq:gemma2-9b-it',
    system_prompt=f'''
        You are a SQL assistant for a telecom database. 
        You generate SQL queries based on user requests. 
        The database schema is:

        {query_generator.DB_SCHEMA}

        Today's date = {date.today()}

        Rules:
        - Use `SELECT` for reading records.
        - Use `INSERT INTO` for adding new records.
        - Use `UPDATE` to modify existing records.
        - Use `DELETE FROM` for removing records.
        - Generate safe, executable SQLite queries.

        Examples:
        {query_generator.SQL_EXAMPLES}
    ''',
    deps_type=Deps,
)
lead_agent = Agent(
    'groq:gemma2-9b-it',
    system_prompt=
        "You are a lead Agent responsible for routing queries to the correct agent."
        "Respond to a geeting and basic questions."
        "Use `delegate_to_web_agent` for web browsing-related queries. "
        "Use `delegate_to_db_agent` for database-related queries. "
        # "In case you do not understand the query just reply - 'Sorllama-3.1-8b-instantry I did'nt understand you!😓'"
)

@lead_agent.tool_plain
async def delegate_to_web_agent(query: str):
    print(f"🔠 Delegating to Web Agent: {query}")
    result = await web_agent.run(query)
    return result.data


@lead_agent.tool_plain
async def delegate_to_db_agent(query: str):
    print(f"📊 Delegating to Database Agent: {query}")
    conn = sqlite3.connect('users.db')
    deps = Deps(conn)
    result = await db_agent.run(query, deps=deps)
    sql_query = re.sub(r"^```sql\s*|\s*```$", "", result.data).strip()
    print(f"Executing Query: {sql_query}") 
    cursor = conn.cursor()
    cursor.execute(sql_query)
    
    if re.match(r"^SELECT", sql_query, re.IGNORECASE):
        rows = cursor.fetchall()
        conn.close()
        return rows
    else:
        conn.commit()
        conn.close()
        return "Query Executed Successfully"

lead_agent.tools = [delegate_to_web_agent, delegate_to_db_agent]

# message_hist = []
# while True:
#     try:
#         curr_msg = input('👦 ')
#         if curr_msg == 'quit':
#             break
#         response = lead_agent.run_sync(curr_msg, message_history=message_hist)
#         message_hist = response.new_messages()
#         print("🤖 ",response.data)
#     except Exception as e:
#         print("Error : ", str(e))

response = lead_agent.run_sync("show me records where the country is 'India'")
print(response.data)