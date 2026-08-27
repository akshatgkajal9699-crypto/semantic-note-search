import psycopg2
from fastembed import TextEmbedding

# 1. Fill in your Railway credentials
PGHOST = "acela.proxy.rlwy.net"
PGPORT = "31056"
PGUSER = "postgres"
PGPASSWORD = "plFxOQgJcxDoZNLmdVQlXOvCsPbOKjbq"
PGDATABASE = "railway"

# Load lightweight embedding model (outputs 384-dim vectors)
print("Loading embedding model...")
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

print("Connecting to database...")
conn = psycopg2.connect(
    host=PGHOST,
    port=PGPORT,
    user=PGUSER,
    password=PGPASSWORD,
    dbname=PGDATABASE
)
cur = conn.cursor()

# 2. Recreate recipes table to match 384 dimensions
print("Updating table schema for 384 dimensions...")
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
cur.execute("DROP TABLE IF EXISTS recipes;")
cur.execute("""
    CREATE TABLE recipes (
        id SERIAL PRIMARY KEY,
        title TEXT,
        description TEXT,
        embedding vector(384)
    );
""")

# 3. Recipe dataset
recipes = [
    {
        "title": "Spicy Arrabbiata Pasta",
        "description": "A quick and fiery Italian pasta with red chili flakes, garlic, and crushed tomatoes. Ready in 15 minutes."
    },
    {
        "title": "Creamy Mushroom Risotto",
        "description": "Rich and comforting slow-cooked arborio rice with butter, parmesan, and wild sauteed mushrooms."
    },
    {
        "title": "Thai Green Chicken Curry",
        "description": "Authentic spicy coconut curry infused with lemongrass, green chilies, basil, and tender chicken strips."
    },
    {
        "title": "Avocado Toast with Poached Egg",
        "description": "Simple fast breakfast featuring mashed ripe avocado on toasted sourdough topped with a runny poached egg."
    }
]

print("Generating embeddings and populating database...")

for item in recipes:
    embeddings = list(model.embed([f"{item['title']}: {item['description']}"]))
    embedding_vector = embeddings[0].tolist()

    cur.execute(
        "INSERT INTO recipes (title, description, embedding) VALUES (%s, %s, %s::vector)",
        (item["title"], item["description"], str(embedding_vector))
    )

conn.commit()
cur.close()
conn.close()

print("Database seeded successfully!")
