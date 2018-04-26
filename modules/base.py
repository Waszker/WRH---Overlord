class ModuleBase:
    """
    Abstract base class for WRH modules.
    """
    WRHID = ''
    __abstract__ = True
    tornado_form = (r'^some_path/$', None)
    html_repr = ''

    @classmethod
    def get_html(cls, module):
        """
        Return html string for placing it on the Tornado web page.
        :param module: instance of module object from database
        :return: html-formatted string
        :rtype: str
        """
        raise NotImplemented('Must declare function body!')

    @classmethod
    async def parse_request(cls, session, request_string):
        """
        Parse request and return proper data.
        This is asynchronous coroutine meant to be invoked by Tornado server.
        :param session: database connection session
        :param request_string: request string sent via request
        :return: result in form of string
        :rtype: str
        """
        raise NotImplemented('Must declare function body!')

    @classmethod
    def get_object(cls, measurement_object):
        """
        Create specific Measurement object
        :param measurement_object:
        :return:
        """
        raise NotImplemented('Must declare function body!')
