import os
from importlib import import_module
from os.path import join as pjoin
from sqlalchemy.ext.declarative import declarative_base

from db_engine.constants import ADDITIONAL_DB_MODULES_PATH
from utils.io import log

Base = declarative_base()


def __scan_and_load_wrh_modules(path):
    if not os.path.exists(path):
        log(f'Path {path} for additional WRH modules does not exist')
        return ()

    from modules.base import ModuleBase
    classes = []
    for mdir in (e for e in os.listdir(path) if e[0] != '.' and os.path.isdir(pjoin(path, e))):
        _path = pjoin(path, mdir)
        if '__init__.py' not in os.listdir(_path): continue
        module_files = (f for f in os.listdir(_path) if f[0] != '.' and f != '__init__.py' and f[-3:] == '.py')
        modules = [import_module(str(pjoin(_path, m)).replace(os.sep, '.')[:-3]) for m in module_files]
        attributes = [getattr(module, attr) for module in modules for attr in module.__dict__]
        classes.extend(attr for attr in attributes if isinstance(attr, type) and
                       issubclass(attr, ModuleBase) and issubclass(attr, Base) and getattr(attr, 'WRHID', None))
    return tuple(classes)


WRH_MODULES = __scan_and_load_wrh_modules(ADDITIONAL_DB_MODULES_PATH)
