import optparse

from soma import aims


def same_graphs(ref_graph_filename, test_graph_filename, verbose=False):

    ref_graph = _read_graph(ref_graph_filename) 
    test_graph = _read_graph(test_graph_filename) 

    ref_vertices = _build_vertice_dictionary(ref_graph)
    test_vertices = _build_vertice_dictionary(test_graph)

    if verbose: print "Compare vertices:"
    if not _same_dictionary(ref_vertices, test_vertices, _same_vertice, verbose): 
        if verbose: print "  differences in vertices"
        return False

    ref_edges = _build_edge_dictionary(ref_graph)
    test_edges = _build_edge_dictionary(test_graph)

    if verbose: print "Compare edges:"
    if not _same_dictionary(ref_edges, test_edges, _same_edge, verbose):
        if verbose: print "  differences in edges"
        return False

    return True


def _read_graph(filename):
    graph = aims.read(filename)
    return graph


def _build_vertice_dictionary(graph):
    vertice_dict = {}
    for vertice in graph.vertices():
        vertice_dict[vertice['index']] = vertice
    return vertice_dict


def _build_edge_dictionary(graph):
    edge_dict = {} 
    for edge in graph.edges():
        index = (edge.vertices()[0]['index'], edge.vertices()[1]['index'], edge.getSyntax())
        assert(index not in edge_dict)
        edge_dict[index] = edge
    return edge_dict


def _same_dictionary(ref_dict, test_dict, same_element_function, verbose=False):
    if verbose: 
        print "  first:  " + str(len(ref_dict)) + " elements."
        print "  second: " + str(len(test_dict)) + " elements."
    if not len(ref_dict) == len(test_dict):
        if verbose: 
            print "  different number of elements."
        return False
    for index, ref in ref_dict.iteritems():
        if index not in test_dict:
            if verbose: print "  test dict has no element with index " +  repr(index)
            same_dict = False
            break       
        same_dict = same_element_function(ref, test_dict[index], verbose)
        if not same_dict: 
            if verbose: print "difference in " + repr(index)
            break
    return same_dict


def _same_vertice(ref_vertice, test_vertice, verbose):
    if not len(ref_vertice) == len(test_vertice):
        if verbose:
            print "  different number of arguments " + repr(len(ref_vertice)) + " " + repr(len(test_vertice))
        return False
    for key in ref_vertice.keys():
        if key not in test_vertice:
            if verbose: print repr(key) + " not in test_vertice"
            return False  
        if key not in ['aims_bottom', 'aims_other', 'aims_ss', 'aims_Tmtktri', 
                       'bottom_label', 'other_label', 'ss_label', 'Tmtktri_label']:
            # XXX ref_vertice and test_vertice should be compared directly
            if str(ref_vertice[key]) != str(test_vertice[key]):
                if verbose:
                    print "vertice " + repr(key) + " " + str(ref_vertice[key]) + " " + str(test_vertice[key])
                return False
    return True


def _same_edge(ref_edge, test_edge, verbose):
    # TODO remove the duplication with same_vertice
    same = len(ref_edge) == len(test_edge)
    if not same:
        if verbose:
            print "different numbers of arguments " + repr(len(ref_edge)) + " " + repr(len(test_edge))
        return False
    for key in ref_edge.keys():
        if key not in test_edge:
            if verbose: print repr(key) + " not in test_edge"
            return False  
        if key not in ['aims_cortical', 'aims_junction', 'aims_plidepassage', 
                       'cortical_label', 'junction_label', 'plidepassage_label']:
            # XXX ref_edge and test_edge should be compared directly
            if str(ref_edge[key]) != str(test_edge[key]):
                if verbose:
                    print "edge " + repr(key) + " " + str(ref_edge[key]) + " " + str(test_edge[key])
                return False
    return True


if __name__ == '__main__':
    parser = optparse.OptionParser(usage='%prog ref_graph_filename test_graph_filename')
    parser.add_option('-v', '--verbose', dest="verbose", default=False, action="store_true",
                      help='displays information in the standard output')
    option, args = parser.parse_args()  
    if len(args) != 2:
        parser.error('Graph comparison takes two arguments: the file names of the two graphs.') 

    ref_graph_filename, test_graph_filename = args

    same = same_graphs(ref_graph_filename, test_graph_filename, option.verbose)
    print same


