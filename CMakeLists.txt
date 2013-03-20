cmake_minimum_required( VERSION 2.6 )
find_package( brainvisa-cmake REQUIRED )
BRAINVISA_PROJECT()

BRAINVISA_COPY_PYTHON_DIRECTORY( "${CMAKE_CURRENT_SOURCE_DIR}/morphologist"
                                 ${PROJECT_NAME}
                                 python/morphologist )

BRAINVISA_COPY_FILES( ${PROJECT_NAME} "morphologist-ui.py"
						SOURCE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
						DESTINATION bin)
                          


