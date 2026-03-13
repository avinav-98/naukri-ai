from backend.database import initialize_database
from backend.config import MAIN_DATABASE_PATH


def main():
    initialize_database()
    print(f"Database initialization completed: {MAIN_DATABASE_PATH}")


if __name__ == "__main__":
    main()
