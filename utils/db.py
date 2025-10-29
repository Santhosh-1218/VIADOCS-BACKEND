from flask import current_app

def get_db():
    """
    Safely returns the connected MongoDB database instance from Flask app.
    """
    try:
        db = getattr(current_app, "db", None)
        # ✅ Compare correctly (MongoDB objects don't support bool())
        if db is None:
            raise Exception("Database not initialized in Flask app")
        return db
    except Exception as e:
        print("❌ get_db() error:", e)
        raise
