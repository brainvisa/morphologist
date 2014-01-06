cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

BRAINVISA_FIND_PACKAGE( morphologist-private REQUIRED )
BRAINVISA_FIND_PACKAGE( morphologist-gpl REQUIRED )

BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-private" RUN ">= ${morphologist-private_VERSION_MAJOR}.${morphologist-private_VERSION_MINOR}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-gpl" RUN ">= ${morphologist-gpl_VERSION_MAJOR}.${morphologist-gpl_VERSION_MINOR}" )

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/morphologist"
    ${PROJECT_NAME}
    python/morphologist )

BRAINVISA_ADD_EXECUTABLE( "morphologist-ui.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/morphologist-ui.py" IS_SCRIPT )

