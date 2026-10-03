from player_scouting.infrastructure.persistence.settings import Settings


def test_a_hosted_postgres_url_is_used_with_the_psycopg_driver():
    # Neon and Supabase hand out plain postgres URLs; SQLAlchemy needs the driver.
    neon = Settings(
        database_url="postgresql://u:p@ep-x-pooler.eu.aws.neon.tech/db?sslmode=require"
    )
    short = Settings(database_url="postgres://u:p@host/db")

    assert neon.database_url == (
        "postgresql+psycopg://u:p@ep-x-pooler.eu.aws.neon.tech/db?sslmode=require"
    )
    assert short.database_url == "postgresql+psycopg://u:p@host/db"


def test_a_url_that_already_names_the_driver_is_kept():
    url = "postgresql+psycopg://scouting:scouting@localhost:5433/scouting"

    assert Settings(database_url=url).database_url == url
