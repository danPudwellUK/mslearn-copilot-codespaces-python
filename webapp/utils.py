from contextlib import contextmanager


@contextmanager
def db_session(get_db_fn):
    """Context manager that opens a database connection and ensures it is
    closed when the block exits, even if an exception is raised.

    Parameters:
        get_db_fn: Callable that returns a database connection.

    Yields:
        The database connection returned by ``get_db_fn``.
    """
    conn = get_db_fn()
    try:
        yield conn
    finally:
        conn.close()
