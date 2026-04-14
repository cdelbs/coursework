#lang dssl2
import 'project-lib/dictionaries.rkt'
import 'project-lib/graph.rkt'
import 'project-lib/binheap.rkt'
import 'project-lib/stack-queue.rkt'

# Final project: Trip Planner
import cons
import sbox_hash

### Basic Types ###
#  - Latitudes and longitudes are numbers:
let Lat?  = num?
let Lon?  = num?
#  - Point-of-interest categories and names are strings:
let Cat?  = str?
let Name? = str?
### Raw Item Types ###
#  - Raw positions are 2-element vectors with a latitude and a longitude
let RawPos? = TupC[Lat?, Lon?]
#  - Raw road segments are 4-element vectors with the latitude and
#    longitude of their first endpoint, then the latitude and longitude
#    of their second endpoint
let RawSeg? = TupC[Lat?, Lon?, Lat?, Lon?]
#  - Raw points-of-interest are 4-element vectors with a latitude, a
#    longitude, a point-of-interest category, and a name
let RawPOI? = TupC[Lat?, Lon?, Cat?, Name?]
### Contract Helpers ###
# ListC[T] is a list of `T`s (linear time):
let ListC = Cons.ListC
# List of unspecified element type (constant time):
let List? = Cons.list?

interface TRIP_PLANNER:
    # Returns the positions of all the points-of-interest that belong to
    # the given category.
    def locate_all(
            self,
            dst_cat:  Cat?           # point-of-interest category
        )   ->        ListC[RawPos?] # positions of the POIs
    # Returns the shortest route, if any, from the given source position
    # to the point-of-interest with the given name.
    def plan_route(
            self,
            src_lat:  Lat?,          # starting latitude
            src_lon:  Lon?,          # starting longitude
            dst_name: Name?          # name of goal
        )   ->        ListC[RawPos?] # path to goal
    # Finds no more than `n` points-of-interest of the given category
    # nearest to the source position.
    def find_nearby(
            self,
            src_lat:  Lat?,          # starting latitude
            src_lon:  Lon?,          # starting longitude
            dst_cat:  Cat?,          # point-of-interest category
            n:        nat?           # maximum number of results
        )   ->        ListC[RawPOI?] # list of nearby POIs

        
# Priority Queue structure        
struct PQ:
    let element # value
    let priority # lower weight indicates higher priority

###
### HELPER METHODS ###
###
 
# Returns True if given raw position exists in given list of raw road positions
def contains(l: ListC[RawPos?], p: RawPos?) -> bool?:
    if l == None:
        return False
    elif l.data == p:
        return True
    else:
        contains(l.next, p)

test 'contains() returns False if given empty linked-list':
    assert contains(None, [0,5]) == False  
test 'contains() test':
    let l = cons([0,3],cons([0,4],cons([0,5],None)))
    assert contains(l,[0,5]) == True 
    assert contains(l,[1,5]) == False
    assert contains(l,[0,3]) == True
    assert contains(l,[3,0]) == False
    
# Purpose: To return a vector containing vertex distances [0] and predecessors [1]
# Assumption: Given start node exists in graph
def dijkstraPQ(graph: WUGraph?, start) -> TupC[vec?,vec?]:
    let pred = [None;graph.len()]
    let dist = [inf;graph.len()]
    dist[start] = 0
    let todo = BinHeap[PQ?](graph.len(), lambda x, y: x.priority <= y.priority)
    let done = [False;graph.len()]
    todo.insert(PQ(start,0))
    while todo.len() > 0:
        let v = todo.find_min().element
        todo.remove_min()
        if done[v]==False:
            done[v]=True
            for u in Cons.to_vec(graph.get_adjacent(v)):
                if dist[v] + graph.get_edge(v,u) < dist[u]:
                    dist[u] = dist[v] + graph.get_edge(v,u)
                    pred[u] = v
                    todo.insert(PQ(u,dist[u]))
    return [dist, pred]

 
test 'dijkstraPQ test 1':
    let graph = WUGraph(6)
    graph.set_edge(0,1,12)
    graph.set_edge(1,2,31)
    graph.set_edge(2,4,2)
    graph.set_edge(2,5,7)
    graph.set_edge(4,3,9)
    graph.set_edge(3,5,1)
    graph.set_edge(3,1,56)
    assert dijkstraPQ(graph, 0)[0] == [0,12,43,51,45,50]
    assert dijkstraPQ(graph, 0)[1] == [None,0,1,5,2,2]
    
    
test 'dijkstraPQ test 2':
    let graph = WUGraph(6)
    graph.set_edge(0,4,14)
    graph.set_edge(0,5,9)
    graph.set_edge(0,1,7)
    graph.set_edge(4,5,2)
    graph.set_edge(4,3,9)
    graph.set_edge(5,1,10)
    graph.set_edge(5,2,11)
    graph.set_edge(1,2,15)
    graph.set_edge(3,2,6)
    assert dijkstraPQ(graph,0)[0] == [0,7,20,20,11,9]
    assert dijkstraPQ(graph,0)[1] == [None,0,5,4,5,0]


    
# Purpose: To return the shortest path from the given start vertex
#          to the given end vertex using the given list of predecessors
# Assumption: Given list of predecessors is not empty
def find_path(start: Vertex?, end: Vertex?, lopred: vec?) -> ListC[Vertex?]:      
    if lopred[end] == None and start != end:
        return None
    let ret = cons(end, None)
    let pointer = end
    while pointer != start:
        let p = lopred[pointer]
        ret = cons(p, ret)
        pointer = p
    return ret 
    
test 'find_path works on same start/end vertex':
    let v = [None,0,1,5,2,2]
    assert Cons.to_vec(find_path(0,0,v)) == [0]
    
test 'complex find_path test':
    let v1 = [None,0,1,5,2,2]
    let v2 = [None,0,5,4,5,0]
    assert Cons.to_vec(find_path(0,3,v1)) == [0,1,2,5,3]
    assert Cons.to_vec(find_path(0,4,v1)) == [0,1,2,4]
    
    assert Cons.to_vec(find_path(0,5,v2)) == [0,5]
    assert Cons.to_vec(find_path(0,3,v2)) == [0,5,4,3]
    
test 'find_path and dijkstraPQ test':
    let dg = WUGraph(6)
    dg.set_edge(0,1,7)
    dg.set_edge(0,5,9)
    dg.set_edge(0,4,14)
    dg.set_edge(1,5,10)
    dg.set_edge(1,2,15)
    dg.set_edge(2,5,11)
    dg.set_edge(2,3,6)
    dg.set_edge(3,4,9)
    dg.set_edge(4,5,2)
    let pred = dijkstraPQ(dg,0)[1]
    assert Cons.to_vec(find_path(0,3,pred)) == [0,5,4,3]
    assert Cons.to_vec(find_path(0,5,pred)) == [0,5]
    assert Cons.to_vec(find_path(0,2,pred)) == [0,5,2]
        
###
### HELPER METHODS FOR INITIALIZING TripPlanner ###
###
            
# Returns vector of unique positions in the given vector of raw road segments
def parse_segments(segments: VecC[RawSeg?]) -> VecC[RawPos?]:
    if segments.len() == 0:
        return error('Trip Planner was initialized with no positions')
    let ret = None
    for seg in segments:
        if not contains(ret, [seg[0], seg[1]]):
            ret = cons([seg[0], seg[1]], ret)
        if not contains(ret, [seg[2], seg[3]]):
            ret = cons([seg[2], seg[3]], ret)
    return Cons.to_vec(ret)
    
test 'parse_segments() error':
    assert_error TripPlanner([],[])
    
test 'parse_segments() test':
    let v1 = [[0,1,2,3],[2,1,3,4],[3,2,3,4]]
    let v2 = [[2,1,3,4],[0,1,2,3],[3,2,3,4]]
    assert parse_segments(v1) == [[3,2],[3,4],[2,1],[2,3],[0,1]]
    assert parse_segments(v2) == [[3,2], [2,3], [0,1], [3,4], [2,1]]
    
# Returns the Euclidean distance between given latitudes and longitudes 
def distance(lat1: Lat?, long1: Lon?, lat2: Lat?, long2: Lon?) -> num?:
    return (((long2 - long1)**2 + (lat2 - lat1)**2)**0.5) 
    
test 'distance() test':
    assert distance(0,2,4,2) == 4.0
    assert distance(-12,6,4,12).floor() == 17
    assert distance(-5.2,7,1,3).floor() == 7



# Trip Planner API
class TripPlanner (TRIP_PLANNER):
    let map: WUGraph?
    let endpoint_to_nodeid: HashTable?
    let nodeid_to_endpoint: VecC[RawPos?]
    let pois: VecC[RawPOI?]
 
    ### CONSTRUCTOR ###
    def __init__(self, road_segments: VecC[RawSeg?], pois: VecC[RawPOI?]):
        # Vector of unique raw positions on the map
        # Also, maps each index(node) to an endpoint
        self.nodeid_to_endpoint = parse_segments(road_segments)
        # Vector of raw points of interests
        self.pois = pois
        # Map
        self.map = WUGraph(self.nodeid_to_endpoint.len())
        # Mapping endpoint to node
        self.endpoint_to_nodeid = HashTable(self.map.len(), make_sbox_hash())
        for i in range(self.map.len()):
            self.endpoint_to_nodeid.put(self.nodeid_to_endpoint[i], i)

        # Initialize Map with edges, weights representing Euclidean distance between endpoints
        for seg in road_segments:
            self.map.set_edge(self.endpoint_to_nodeid.get([seg[0], seg[1]]), self.endpoint_to_nodeid.get([seg[2], seg[3]]), \
            distance(seg[0], seg[1], seg[2], seg[3]))

    ###
    ### METHODS ###
            
    # Returns the positions of all the points-of-interest that belong to
    # the given category.             
    def locate_all(self, dst_cat: Cat?) -> ListC[RawPos?]:
        let ret = None
        for poi in self.pois:
            if not contains(ret,[poi[0],poi[1]]) and poi[2] == dst_cat:
                ret = cons([poi[0],poi[1]],ret)
        return ret

     
    # Returns the shortest route, if any, from the given source position
    # to the point-of-interest with the given name.
    # Assumption: Only one point of interest has the given name
    def plan_route(self, src_lat:Lat?, src_lon:Lon?, dst_name:Name?) -> ListC[RawPos?]:
        let target_poi = self.pois.filter(lambda x: x[3] == dst_name)
        if target_poi.len() == 0:
            return None
        else:
            target_poi = target_poi[0]
            let start = [src_lat, src_lon]
            let shortest_paths = dijkstraPQ(self.map, self.endpoint_to_nodeid.get(start))
        
            let output = find_path(self.endpoint_to_nodeid.get(start),\
            self.endpoint_to_nodeid.get([target_poi[0],target_poi[1]]),shortest_paths[1])
        
            return Cons.map(self.nodeid_to_endpoint.get,output)

    # Finds no more than `n` points-of-interest of the given category
    # nearest to the source position.
    def find_nearby(self, src_lat:Lat?, src_lon:Lon?, dst_cat:Cat?, n:nat?) -> ListC[RawPOI?]:
        let v = self.pois.filter(lambda x: x[2] == dst_cat)
        let dist = dijkstraPQ(self.map, self.endpoint_to_nodeid.get([src_lat,src_lon]))[0]
        v = v.filter(lambda x: dist[self.endpoint_to_nodeid.get([x[0],x[1]])] != inf)
        heap_sort(
                v,
                (lambda x, y: dist[self.endpoint_to_nodeid.get([x[0],x[1]])] <= dist[self.endpoint_to_nodeid.get([y[0],y[1]])]))

        let ret = [v[i] for i in range(min(n,v.len()))]
        return Cons.from_vec(ret)

 
###
### SAMPLE TRIP PLANNERS FOR TESTING ###
###
        
# First Trip Planner for basic testing
def basic_trip_planner():
    return TripPlanner([[0,0, 0,1], [0,0, 1,0]],
                       [[0,0, "bar", "The Empty Bottle"],
                        [0,1, "food", "Pierogi"]])

# Trip Planner example from assignment prompt                        
def trip_planner_from_prompt():
    return TripPlanner([[0,0,1,0],[0,0,0,1],[0,1,0,2],[0,1,1,1],[1,0,1,1],[1,1,1,2],[0,2,1,2],[1,2,1,3],[-0.2,3.3,1,3]],\
     [[0,0,"food","Sandwiches"],[0,1,"food","Pasta"],[0,1,"clothes","Pants"],[1,1,"bank","Local Credit Union"],[-.2,3.3,"food","Burritos"],\
     [1,3,"bar","Bar None"],[1,3,"bar","H Bar"]])

# Trip Planner example from assignment prompt with isolated positions and points of interests
def trip_planner_with_disconnected_pois():
    return TripPlanner([[0,0,1,0],[0,0,0,1],[0,1,0,2],[0,1,1,1],[1,0,1,1],[1,1,1,2],[0,2,1,2],[1,2,1,3],[-0.2,3.3,1,3],\
    [4,0,3,0],[5,0,3,0],[4,1,4,0]],\ # Disconnected
     [[0,0,"food","Sandwiches"],[0,1,"food","Pasta"],[0,1,"clothes","Pants"],[1,1,"bank","Local Credit Union"],[-.2,3.3,"food","Burritos"],\
     [1,3,"bar","Bar None"],[1,3,"bar","H Bar"],\
     [4,1,'bar','Far Bar'],[5,0,'food','Far Food']])

     
###
### TESTS FOR TRIP PLANNER METHODS ###
###
     

test 'locate_all on basic_tp':
    let tp = basic_trip_planner()
    assert Cons.to_vec(tp.locate_all("food")) == [[0,1]]
        
test 'locate_all on tp_from_prompt':
    let tp = trip_planner_from_prompt()
    assert Cons.to_vec(tp.locate_all("bank")) == [[1,1]] #No duplicates
    assert Cons.to_vec(tp.locate_all("bar")) == [[1,3]]
    assert Cons.to_vec(tp.locate_all("food")) == [[-0.2,3.3],[0,1],[0,0]] # at different endpoints
    assert Cons.to_vec(tp.locate_all("doesnt exist")) == [] # No pois of given category 

test 'locate_all on tp_with_disconnected_pois':
    let tp = trip_planner_with_disconnected_pois()
    assert Cons.to_vec(tp.locate_all('food')) == [[5,0],[-0.2,3.3],[0,1],[0,0]] # Includes all positions, connected or not
    assert Cons.to_vec(tp.locate_all('bar')) == [[4,1],[1,3]]
       
    
test 'plan_route on basic_tp':
    let tp = basic_trip_planner()
    assert Cons.to_vec(tp.plan_route(0, 0, "Pierogi")) == [[0,0],[0,1]]
    
test 'plan_route on tp_from_prompt':
    let tp = trip_planner_from_prompt()
    assert Cons.to_vec(tp.plan_route(1,1,'Non Existent')) == [] # Returns empty if destination does not exist
    assert Cons.to_vec(tp.plan_route(1,1,'Local Credit Union')) == [[1,1]] # If destination is at given position
    assert Cons.to_vec(tp.plan_route(0,0,'Burritos')) == [[0,0],[0,1],[0,2],[1,2],[1,3],[-0.2,3.3]]
    assert Cons.to_vec(tp.plan_route(0,2,'Sandwiches')) == [[0,2],[0,1],[0,0]] 

test 'plan_route on tp_with_disconnected_pois':
    let tp = trip_planner_with_disconnected_pois()
    assert Cons.to_vec(tp.plan_route(0,0,'Far Bar')) == [] # Returns empty if destination is unreachable
    assert Cons.to_vec(tp.plan_route(3,0,'Far Food')) == [[3,0],[5,0]] # plan_route on a disconnected chunk of positions

    
test 'find_nearby on basic_tp':
    let tp = basic_trip_planner()
    assert Cons.to_vec(tp.find_nearby(0,0,'food',0)) == [] # Returns empty if given limit is 0
    assert Cons.to_vec(tp.find_nearby(0,0,'game store',3)) == [] # Returns empty if no poi with given category is nearby
    assert Cons.to_vec(tp.find_nearby(0, 0, "food", 1)) == [[0,1,'food','Pierogi']]

test 'find_nearby on tp_from_prompt':
    let tp =  trip_planner_from_prompt()
    assert Cons.to_vec(tp.find_nearby(0,0,'food',2)) == [[0,0,'food','Sandwiches'],[0,1,'food','Pasta']]
    assert Cons.to_vec(tp.find_nearby(0,0,'bar',5)) == [[1,3,'bar','H Bar'],[1,3,'bar','Bar None']] # Less pois than limit

test 'find_nearby on tp_with_disconnected_pois':
    let tp = trip_planner_with_disconnected_pois()
    assert Cons.to_vec(tp.find_nearby(0,0,'food',4)) == [[0,0,'food','Sandwiches'],[0,1,'food','Pasta'],\
                                                        [-.2,3.3,"food","Burritos"]] # Does not acount include unreachable pois
    assert Cons.to_vec(tp.find_nearby(3,0,'bar',2)) == [[4,1,'bar','Far Bar']] # find_nearby on tp_with_disconnected_pois
    
 
    

