import os

from pybuilder.core import use_plugin
from pybuilder.core import init

# This must be as the first one!!!
use_plugin("pypi:pybuilder_setup_cfg", "~=0.0.17")

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("copy_resources")
use_plugin("filter_resources")
use_plugin("exec")
use_plugin("python.sphinx")
use_plugin('pypi:pybuilder_pytest', "~=1.2.0")
use_plugin("pypi:pybuilder_pytest_coverage")
use_plugin("python.flake8")
use_plugin("pypi:pybuilder_scm_ver_plugin", "~=0.2.1")
use_plugin("pypi:pybuilder_stubs_package")
use_plugin("pypi:pybuilder_smart_copy_resources")

RELEASES_DIR = "releases/"
SRC_DIR = "src/"
UNIT_TESTS_DIR = "unit_tests/"
INTEGRATION_TESTS_DIR = "integration_tests/"
DOC_DIR = "doc/"
DOC_FORMAT = "html"
REPORTS_DIR = "reports/"

@init
def set_properties(project):
    project.set_property("dir_source_main_python", SRC_DIR)
    project.set_property("dir_docs", DOC_DIR)
    project.set_property("dir_reports", REPORTS_DIR)

    build_dir = os.path.join(RELEASES_DIR, "$name-$version")

    project.set_property("dir_dist", build_dir)

    project.set_property("copy_resources_target", build_dir)

    # Configure sphinx for documentation generation
    project.set_property("sphinx_builder", DOC_FORMAT)
    project.set_property("sphinx_config_path", os.path.join(DOC_DIR, "source"))
    project.set_property("sphinx_source_dir", os.path.join(DOC_DIR, "source"))
    project.set_property("sphinx_output_dir", os.path.join(DOC_DIR, "build", DOC_FORMAT))

    # Used to replace some placeholder in the specified files, e.g.
    # ${version} or ${some_property}
    project.set_property("filter_resources_target", build_dir)
    project.set_property("filter_resources_glob", [
        os.path.join("**", "__init__.py")
    ])

    project.depends_on_requirements("requirements.txt")
    project.build_depends_on_requirements("requirements-dev.txt")

    project.set_property("flake8_break_build", True)
    project.set_property("flake8_verbose_output", True)

    # PyTest unit tests via a plugin
    project.set_property("dir_source_pytest_python", UNIT_TESTS_DIR)

    # PyTest integration tests via a plugin
    project.set_property("dir_source_pytest_integration_python", INTEGRATION_TESTS_DIR)
    project.set_property("integrationtest_file_glob", "test_*")

    # Settings for stubgen
    project.set_property("stubs_include_docstrings", True)
    project.set_property("stubs_include_private", True)
