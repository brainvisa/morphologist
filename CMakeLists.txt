cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

BRAINVISA_FIND_PACKAGE( morphologist-private REQUIRED )
BRAINVISA_FIND_PACKAGE( morphologist-gpl REQUIRED )

BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-private" RUN ">= ${morphologist-private_VERSION_MAJOR}.${morphologist-private_VERSION_MINOR}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "morphologist-gpl" RUN ">= ${morphologist-gpl_VERSION_MAJOR}.${morphologist-gpl_VERSION_MINOR}" )
BRAINVISA_DEPENDENCY( RUN DEPENDS "anatomist-gpl" RUN ">= ${anatomist-gpl_VERSION}" )

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
