# -*- coding: utf-8 -*-
import collections
import os

from ordered_dict import OrderedDict


class BidiMap(collections.MutableMapping):
    '''Bi-directional map'''

    def __init__(self, default_keyname='default', reverse_keyname='reverse'):
        super(BidiMap, self).__init__()
        self._map = {}
        self._rmap = {}
        self.default_keyname = default_keyname
        self.reverse_keyname = reverse_keyname
        self.iter_keyname = default_keyname

    def __len__(self):
        return len(self._map)

    def __delitem__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        del first_map[key]
        keys = [k for k, v in snd_map.items() if v == key]
        for k in keys: del snd_map[k]

    def __getitem__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        return first_map[key]

    def __setitem__(self, key_keyname, value):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        first_map[key] = value
        snd_map[value] = key

    def __contains__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        return first_map.__contains__(key)
        
    def __iter__(self):
        first_map, snd_map = self._select_maps(self.iter_keyname)
        for key in first_map:
            yield key

    def _select_maps(self, keyname):
        if keyname is None or keyname == self.default_keyname:
            first_map = self._map
            snd_map = self._rmap
        elif keyname == self.reverse_keyname:
            first_map = self._rmap
            snd_map = self._map
        else:
            raise KeyError(keyname)
        return first_map, snd_map

    def _get_key_keyname(self, key_keyname):
        if isinstance(key_keyname, tuple):
            key, keyname = key_keyname
        else:
            key, keyname = key_keyname, None
        if keyname is None:
            keyname = self.default_keyname
        return key, keyname

    def __str__(self):
        s = "('%s': %s, " % (self.default_keyname, self._map)
        s += "'%s': %s)" % (self.reverse_keyname, self._rmap)
        return s
        

class Graph(object):
    '''
    example : (A is the root node)

    A ----> B -----> C <------------·
    |                               |
    ·-----> D -----> E -----·       |
            |               |       |
            ·------> F -----·-----> G
      
    dependencies : [[1, 3],  # A -> (B, D)
                    [2],     # B -> C
                    [],      # C
                    [4, 5],  # D -> (E, F)
                    [6],     # E -> G
                    [6],     # F -> G
                    [2]]     # G -> C
    data = [A, B, C, D, E, F, G]
    '''

    def __init__(self, dependencies=None, data=None):
        if dependencies is not None:
            self._dependencies = dependencies
        if data:
            self._data = data
        else:
            self._data = [None] * len(self)

    @staticmethod
    def from_soma_workflow(workflow):
        '''
    an additionnal root node is added at index 0 with None data
        '''
        class SWGraphData(object):

            def __init__(self, groupname, job_id):
                self.groupname = groupname
                self.job_id = job_id

        def _find_orphans_nodes(dependencies):
            marks = [False] * len(dependencies)
            marks[0] = True # special case for root nodes
            for deps in dependencies:
                for dep in deps:
                    marks[dep] = True
            orphans_nodes = [i for i, mark in enumerate(marks)
                                            if mark is False]
            return orphans_nodes
        size = len(workflow.jobs) + 1 # add root node
        data = [None] * size
        dependencies = [[] for i in range(size)]
        job_map = {}
        ind = 1 # take into account root node
        for group in workflow.groups:
            for job in group.elements:
                job_id = workflow.job_mapping[job].job_id
                job_map[id(job)] = ind
                data[ind] = SWGraphData(group.name, job_id)
                ind += 1
        for src, dst in workflow.dependencies:
            id_src, id_dst = id(src), id(dst)
            dependencies[job_map[id_dst]].append(job_map[id_src])
        # all orphans nodes are linked to a spurious root node
        dependencies[0] = _find_orphans_nodes(dependencies)
        return Graph(dependencies, data)

    def __len__(self):
        return len(self._dependencies)

    def dependencies(self, node):
        return self._dependencies[node]

    def data(self, node):
        return self._data[node]

    def set_data(self, data):
        assert len(data) == len(self)
        self._data = data

    def __iter__(self):
        for data in self._data:
            yield data

    def breadth_first_coverage(self, func=(lambda n, f : None),
                                     func_extra_data=None):
        marks = [False] * len(self)
        marks[0] = True
        queue = collections.deque([0])
        while len(queue):
            node = queue.popleft()
            continue_graph_coverage = func(self, node, func_extra_data)
            if not continue_graph_coverage: continue # skip dependencies
            for dep in self._dependencies[node]:
                if not marks[dep]:
                    queue.append(dep)
                    marks[dep] = True


def remove_all_extensions(filename):
    name, ext = os.path.splitext(os.path.basename(filename))
    while (ext != ""):
        name, ext = os.path.splitext(name)
    return name


def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


def create_directories_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
