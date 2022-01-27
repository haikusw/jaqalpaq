# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import sys, importlib
from pathlib import Path


def _jaqal_find_spec_relative_to_file(mod_name, jaqal_filename):
    search_path = Path(jaqal_filename).parent

    # Our top preference is a module in a directory:
    try_directory = search_path / mod_name
    if try_directory.is_dir():
        # This does not handle namespace packages
        spec = importlib.util.spec_from_file_location(
            mod_name, try_directory / "__init__.py"
        )
        if spec:
            return spec

    # Our second preference is a module in a file:
    try_file = search_path / f"{mod_name}.py"
    if try_file.is_file():
        spec = importlib.util.spec_from_file_location(mod_name, try_file)
        if spec:
            return spec

    # Our final preference is a python egg:
    import re, os
    from zipimport import zipimporter

    try:
        from packaging import version
    except ImportError:
        import warnings

        warnings.warn('Not searching for Python eggs: "packaging" module not found')
        raise ImportError(f"Unable to find module {mod_name}")

    try_eggs = []
    egg_regexp = re.compile(f"{mod_name}-([^-]*)-(.*)\\.egg")

    for candidate in os.listdir(search_path):
        egg_version = egg_regexp.match(candidate)
        if egg_version:
            # TODO: Also check groups()[1] for Python version compatibility
            try_eggs.append((version.parse(egg_version.groups()[0]), candidate))

    if not try_eggs:
        raise ImportError(f"Unable to find module {mod_name}")

    return importlib.util.spec_from_loader(
        mod_name, zipimporter(search_path / max(try_eggs)[1])
    )


def _jaqal_import_module_relative_to_file(mod_name, jaqal_filename):
    top_level, *module_heirarchy = mod_name.split(".")

    if not jaqal_filename:
        raise ImportError("Unable to perform relative import without jaqal_filename")

    spec = _jaqal_find_spec_relative_to_file(top_level, jaqal_filename)
    module = spec.loader.load_module(top_level)

    return module


def jaqal_import(
    mod_name, obj_name, jaqal_filename, reload_module="relative_only", full_reload=True
):
    assert reload_module in (True, False, "relative_only")

    if mod_name.startswith("."):
        relative = True
        reload_module = not (reload_module is False)
        mod_name = mod_name[1:]
    else:
        relative = False
        reload_module = reload_module is True

    if not mod_name:
        raise ImportError("Module name may not be empty")

    module = sys.modules.get(mod_name)

    if module and reload_module:
        if full_reload:
            del sys.modules[mod_name]
            for k in sys.modules.keys():
                if k.startswith(f"{mod_name}."):
                    del sys.modules[k]
            module = None
        elif relative:
            module = None
        else:
            importlib.reload(module)

    if module is None:
        if relative:
            module = _jaqal_import_module_relative_to_file(mod_name, jaqal_filename)
        else:
            module = importlib.import_module(mod_name)

    try:
        return getattr(module, obj_name)
    except AttributeError:
        submod_name = f"{module.__name__}.{obj_name}"
        ret = sys.modules.get(submod_name)
        if ret and reload_module:
            importlib.reload(ret)

        if ret is None:
            # Because we imported the spec correctly, Python knows how to find
            # the submodules.  In particular, it can probe down into zip files.
            ret = importlib.import_module(submod_name)

        return ret


def get_jaqal_gates(jaqal_module, jaqal_filename=None):
    jg = jaqal_import(str(jaqal_module), "jaqal_gates", jaqal_filename=jaqal_filename)
    return jg.ALL_GATES
