class ModuleBase:
    """
    Abstract base class for WRH modules.
    """
    WRHID = ''
    __abstract__ = True

    @classmethod
    def get_html(cls):
        """
        Return html string for placing it on the Tornado web page.
        :return: html-formatted string
        :rtype: str
        """
        raise AttributeError('Must declare function body!')

    @classmethod
    def get_object(cls, measurement_object):
        """
        Create specific Measurement object
        :param measurement_object:
        :return:
        """
        raise AttributeError('Must declare function body!')
