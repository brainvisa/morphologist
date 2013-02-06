# -*- coding: utf-8 -*-
import sys
import unittest
import optparse

import soma.workflow as sw

from morphologist.runner import SomaWorkflowRunner
from morphologist.utils import Graph


F = False # job failed
OK = True # job success


class D(object):

    def __init__(self, job_id, success):
        self.job_id = job_id
        self.success = success 


class TestGraph(unittest.TestCase):

    def setUp(self):
        pass

    def create_leaf_graph(self, data):
        '''
    Root -> (1, ·)
        '''
        dependencies = [[1], []]
        return Graph(dependencies, data)

    def create_chain_graph_1(self, data):
        '''
    Root -> (1, ·) -> (2, ·)
        '''
        dependencies = [[1], [2], []]
        return Graph(dependencies, data)

    def create_chain_graph_2(self, data):
        '''
    Root -> (1, ·) -> (2, ·) -> (3, ·) -> (4, ·)
        '''
        dependencies = [[1], [2], [3], [4], []]
        return Graph(dependencies, data)

    def create_tree_graph_1(self, data):
        '''
    Root -> (1, ·) -> (2, ·)
                   -> (3, ·)
        '''
        dependencies = [[1], [2, 3], [], []]
        return Graph(dependencies, data)

    def create_root_triangle_graph(self, data):
        '''
    Root ----------·-> (1, ·)
      |            |
      ·-> (2, ·) --·
        '''
        dependencies = [[1, 2], [], [1]]
        return Graph(dependencies, data)

    def create_triangle_graph(self, data):
        '''
    Root -> (1, ·) --------·-> (2, ·)
              |            |
              ·-> (3, ·) --·
        '''
        dependencies = [[1], [2, 3], [], [2]]
        return Graph(dependencies, data)

    def create_diamon_graph(self, data):
        '''
    Root -> (1, ·) -> (2, ·) --·-> (3, ·)
              |                |
              ·-----> (4, ·) --·
        '''
        dependencies = [[1], [2, 4], [3], [], [3]]
        return Graph(dependencies, data)

    def create_complex_graph(self, data):
        '''
    Root -> (1, ·) -> (2, ·) --·-> (3, ·) --·-> (4, ·)
              |                |            |
              ·-----> (5, ·) --·            |
              |          |                  |
              |          ·-------> (6, ·) --·-> (7, ·)
              |          |                  |
              ·-----> (8, ·) ---------------·
        '''
        dependencies = [[1], [2, 5, 8], [3], [4], [],
                        [3], [4, 7], [], [4, 6, 7]]
        return Graph(dependencies, data)

    def test_leaf_graph_test1(self):
        '''
    Root -> (1, F)
        '''
        data = [None, D(1, F)]
        graph = self.create_leaf_graph(data)
        result = [1]
        self._test_graph(graph, result)

    def test_leaf_graph_test2(self):
        '''
    Root -> (1, OK)
        '''
        data = [None, D(1, OK)]
        graph = self.create_leaf_graph(data)
        result = []
        self._test_graph(graph, result)

    def test_chain_graph_1_test1(self):
        '''
    Root -> (1, F) -> (2, OK)
        '''
        data = [None, D(1, F), D(2, OK)]
        graph = self.create_chain_graph_1(data)
        result = [1]
        self._test_graph(graph, result)

    def test_chain_graph_1_test2(self):
        '''
    Root -> (1, OK) -> (2, OK)
        '''
        data = [None, D(1, OK), D(2, OK)]
        graph = self.create_chain_graph_1(data)
        result = []
        self._test_graph(graph, result)

    def test_chain_graph_1_test3(self):
        '''
    Root -> (1, F) -> (2, F)
        '''
        data = [None, D(1, F), D(2, F)]
        graph = self.create_chain_graph_1(data)
        result = [2]
        self._test_graph(graph, result)

    def test_chain_graph_2_test1(self):
        '''
    Root -> (1, F) -> (2, F) -> (3, OK) -> (4, OK)
        '''
        data = [None, D(1, F), D(2, F), D(3, OK), D(4, OK)]
        graph = self.create_chain_graph_2(data)
        result = [2]
        self._test_graph(graph, result)

    def test_tree_graph_1_test1(self):
        '''
    Root -> (1, F) -> (2, F)
                   -> (3, F)
        '''
        data = [None, D(1, F), D(2, F), D(3, F)]
        graph = self.create_tree_graph_1(data)
        result = [2, 3]
        self._test_graph(graph, result)

    def test_tree_graph_1_test2(self):
        '''
    Root -> (1, F) -> (2, OK)
                   -> (3, F)
        '''
        data = [None, D(1, F), D(2, OK), D(3, F)]
        graph = self.create_tree_graph_1(data)
        result = [3]
        self._test_graph(graph, result)

    def test_tree_graph_1_test3(self):
        '''
    Root -> (1, F) -> (2, OK)
                   -> (3, OK)
        '''
        data = [None, D(1, F), D(2, OK), D(3, OK)]
        graph = self.create_tree_graph_1(data)
        result = [1]
        self._test_graph(graph, result)

    def test_tree_graph_1_test4(self):
        '''
    Root -> (1, OK) -> (2, OK)
                    -> (3, OK)
        '''
        data = [None, D(1, OK), D(2, OK), D(3, OK)]
        graph = self.create_tree_graph_1(data)
        result = []
        self._test_graph(graph, result)

    def test_root_triangle_graph_test1(self):
        '''
    Root ----------·-> (1, F)
      |            |
      ·-> (2, F) --·
        '''
        data = [None, D(1, F), D(2, F)]
        graph = self.create_root_triangle_graph(data)
        result = [1]
        self._test_graph(graph, result)

    def test_root_triangle_graph_test2(self):
        '''
    Root ----------·-> (1, OK)
      |            |
      ·-> (2, F) --·
        '''
        data = [None, D(1, OK), D(2, F)]
        graph = self.create_root_triangle_graph(data)
        result = [2]
        self._test_graph(graph, result)

    def test_root_triangle_graph_test3(self):
        '''
    Root ----------·-> (1, OK)
      |            |
      ·-> (2, OK) --·
        '''
        data = [None, D(1, OK), D(2, OK)]
        graph = self.create_root_triangle_graph(data)
        result = []
        self._test_graph(graph, result)

    def test_triangle_graph_test1(self):
        '''
    Root -> (1, F) --------·-> (2, F)
              |            |
              ·-> (3, F) --·
        '''
        data = [None, D(1, F), D(2, F), D(3, F)]
        graph = self.create_triangle_graph(data)
        result = [2]
        self._test_graph(graph, result)

    def test_triangle_graph_test2(self):
        '''
    Root -> (1, F) --------·-> (2, OK)
              |            |
              ·-> (3, F) --·
        '''
        data = [None, D(1, F), D(2, OK), D(3, F)]
        graph = self.create_triangle_graph(data)
        result = [3]
        self._test_graph(graph, result)

    def test_triangle_graph_test3(self):
        '''
    Root -> (1, F) --------·-> (2, OK)
              |            |
              ·-> (3, OK) --·
        '''
        data = [None, D(1, F), D(2, OK), D(3, OK)]
        graph = self.create_triangle_graph(data)
        result = [1]
        self._test_graph(graph, result)

    def test_diamon_graph_test1(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, F)
              |                |
              ·-----> (4, F) --·
        '''
        data = [None, D(1, F), D(2, F), D(3, F), D(4, F)]
        graph = self.create_diamon_graph(data)
        result = [3]
        self._test_graph(graph, result)

    def test_diamon_graph_test2(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, OK)
              |                |
              ·-----> (4, F) --·
        '''
        data = [None, D(1, F), D(2, F), D(3, OK), D(4, F)]
        graph = self.create_diamon_graph(data)
        result = [2, 4]
        self._test_graph(graph, result)

    def test_diamon_graph_test3(self):
        '''
    Root -> (1, F) -> (2, OK) --·-> (3, OK)
              |                 |
              ·-----> (4, F) ---·
        '''
        data = [None, D(1, F), D(2, OK), D(3, OK), D(4, F)]
        graph = self.create_diamon_graph(data)
        result = [4]
        self._test_graph(graph, result)

    def test_diamon_graph_test4(self):
        '''
    Root -> (1, F) -> (2, OK) --·-> (3, OK)
              |                 |
              ·-----> (4, OK) --·
        '''
        data = [None, D(1, F), D(2, OK), D(3, OK), D(4, OK)]
        graph = self.create_diamon_graph(data)
        result = [1]
        self._test_graph(graph, result)

    def test_complex_graph_test1(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, F) --·-> (4, F)
              |                |            |
              ·-----> (5, F) --·            |
              |          |                  |
              |          ·-------> (6, F) --·-> (7, F)
              |          |                  |
              ·-----> (8, F) ---------------·
        '''
        data = [None, D(1, F), D(2, F), D(3, F), D(4, F),
                D(5, F), D(6, F), D(7, F), D(8, F)]
        graph = self.create_complex_graph(data)
        result = [4, 7]
        self._test_graph(graph, result)

    def test_complex_graph_test2(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, F) --·-> (4, OK)
              |                |            |
              ·-----> (5, F) --·            |
              |          |                  |
              |          ·-------> (6, F) --·-> (7, F)
              |          |                  |
              ·-----> (8, F) ---------------·
        '''
        data = [None, D(1, F), D(2, F), D(3, F), D(4, OK),
                D(5, F), D(6, F), D(7, F), D(8, F)]
        graph = self.create_complex_graph(data)
        result = [3, 7]
        self._test_graph(graph, result)

    def test_complex_graph_test3(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, F) --·-> (4, OK)
              |                |            |
              ·-----> (5, F) --·            |
              |          |                  |
              |          ·-------> (6, F) --·-> (7, OK)
              |          |                  |
              ·-----> (8, F) ---------------·
        '''
        data = [None, D(1, F), D(2, F), D(3, F), D(4, OK),
                D(5, F), D(6, F), D(7, OK), D(8, F)]
        graph = self.create_complex_graph(data)
        result = [3, 6]
        self._test_graph(graph, result)

    def test_complex_graph_test4(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, OK) --·-> (4, OK)
              |                |             |
              ·-----> (5, F) --·             |
              |          |                   |
              |          ·-------> (6, F) ---·-> (7, OK)
              |          |                   |
              ·-----> (8, F) ----------------·
        '''
        data = [None, D(1, F), D(2, F), D(3, OK), D(4, OK),
                D(5, F), D(6, F), D(7, OK), D(8, F)]
        graph = self.create_complex_graph(data)
        result = [2, 5, 6]
        self._test_graph(graph, result)

    def test_complex_graph_test5(self):
        '''
    Root -> (1, F) -> (2, F) --·-> (3, OK) --·-> (4, OK)
              |                |             |
              ·-----> (5, F) --·             |
              |          |                   |
              |          ·-------> (6, OK) --·-> (7, OK)
              |          |                   |
              ·-----> (8, F) ----------------·
        '''
        data = [None, D(1, F), D(2, F), D(3, OK), D(4, OK),
                D(5, F), D(6, OK), D(7, OK), D(8, F)]
        graph = self.create_complex_graph(data)
        result = [2, 5, 8]
        self._test_graph(graph, result)

    def _test_graph(self, graph, result):
        failed_jobs = SomaWorkflowRunner._sw_really_failed_jobs_from_dep_graph(graph)    
        failed_jobs_id = [failed_job.job_id for failed_job in failed_jobs]
        self.assertEqual(failed_jobs_id, result)


    def tearDown(self):
        pass

 
if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test', 
                      dest="test", default=None, 
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([TestGraph(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
