def with_session(method):
    """
    Decorator for running method with active session which will be closed automatically after returning from
    that method.
    Decorated class must have sessionmaker field.
    """

    def inner(self, *args, **kwargs):
        session = self.sessionmaker()
        try:
            results = method(self, session, *args, **kwargs)
            session.commit()
        finally:
            session.close()
        return results

    return inner
