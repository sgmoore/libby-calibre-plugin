from typing import TYPE_CHECKING, Dict


if TYPE_CHECKING :
    # get_resources is defined as def get_resources(zfp, name_or_list_of_names, print_tracebacks_for_missing_resources=True):
    # but zfp is pre-filled to be the name of the zip file, so our fake type checking method skips that parameter

    def get_resources(name_or_list_of_names, print_tracebacks_for_missing_resources=True) -> Dict :
        _error()
        return dict()

    def load_translations():
        _error()

    def _error() :
        raise RuntimeError( "This code is for typechecking only and should never be executed " )
