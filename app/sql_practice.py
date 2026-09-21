from app.database import get_connection


conn = get_connection()
cursor = conn.cursor()

cursor.execute(
    """
    SELECT
        v.id AS vehicle_id,
        v.plate_number,
        r.id AS route_id,
        r.name AS route_name
    FROM vehicle AS v
    JOIN route AS r
        ON v.route_id = r.id
    WHERE v.id = ?
    """,
    ("BUS_100",)
)

row = cursor.fetchone()

if row:
    print(dict(row))
else:
    print("Vehicle not found")

conn.close()