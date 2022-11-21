cmake_minimum_required( VERSION 3.10 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

# BRAINVISA_FIND_PACKAGE( morphologist-nonfree REQUIRED )
BRAINVISA_FIND_PACKAGE( morphologist-gpl REQUIRED )
BRAINVISA_FIND_PACKAGE( anatomist-gpl REQUIRED )
BRAINVISA_FIND_PACKAGE( capsul REQUIRED )

BRAINVISA_DEPENDENCY( DEV DEPENDS "${PROJECT_NAME}" RUN "== ${${PROJECT_NAME}_VERSION}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-nonfree" RUN ">= ${morphologist-nonfree_VERSION_MAJOR}.${morphologist-nonfree_VERSION_MINOR}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-gpl" RUN ">= ${morphologist-gpl_VERSION_MAJOR}.${morphologist-gpl_VERSION_MINOR}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "anatomist-gpl" RUN ">= ${anatomist-gpl_VERSION}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "capsul" RUN ">= ${capsul_VERSION}" )

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/morphologist"
    ${PROJECT_NAME}
    python/morphologist )

BRAINVISA_ADD_EXECUTABLE( "morphologist"
    "${CMAKE_CURRENT_SOURCE_DIR}/bin/morphologist" IS_SCRIPT )

find_package( Sphinx )
BRAINVISA_GENERATE_SPHINX_DOC( "doc/sphinx/user"
  "share/doc/morphologist-ui-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}" USER )
BRAINVISA_GENERATE_SPHINX_DOC( "doc/sphinx/dev"
  "share/doc/morphologist-ui-${BRAINVISA_PACKAGE_VERSION_MAJOR}.${BRAINVISA_PACKAGE_VERSION_MINOR}/dev_doc" )
