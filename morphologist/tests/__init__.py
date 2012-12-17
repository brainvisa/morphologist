def ipythonize_test(cls):
    '''
    example to directly use GUI tests within ipython:

    from morphologist import settings
    settings['start_qt_event_loop_for_tests'] = False
    from morphologist.tests import ipythonize_test

    T = ipythonize_test(test_main_window.TestStudyWidgetIntraAnalysis)
    t = T()
    t.setUp()
    t.test_start_main_window()
    '''
    class T(cls):

        def __init__(self, *args, **kwargs):
            super(T, self).__init__(*args, **kwargs)

        def runTest(self, *args, **kwargs):
            pass
    T.__name__ = cls.__name__ + '_ipythonized'
    return T 
