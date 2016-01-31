import itertools
import random
import parameters
from gradient import localMaximum


def memoize(f):
   cache = {}

   def memoizedFunction(*args):
      if args not in cache:
         cache[args] = f(*args)
      return cache[args]

   memoizedFunction.cache = cache
   return memoizedFunction


def getGraphs(filename):
   with open(filename, 'r') as graphFile:
      lines = graphFile.readlines()

   pairs = lambda L: tuple(L[i:i+2] for i in range(0, len(L)-1, 2))
   intEdges = lambda L: tuple((int(i), int(j)) for i,j in L)

   graphStrings = [(info.strip().split(), pairs(edges.strip().split())) for (info, edges) in pairs(lines)]
   graphInfo = tuple((int(x[0]), int(x[1])) for x,_ in graphStrings)
   graphEdges = tuple(intEdges(edgeList) for _,edgeList in graphStrings)
   return tuple(zip(graphInfo, graphEdges))


def properColoring(edges, colors):
   for e in edges:
      if colors[e[0]] == colors[e[1]]:
         return False
   return True


def numBadEdges(edges, colors):
   count = 0
   for e in edges:
      if colors[e[0]] == colors[e[1]]:
         count += 1
   return count


def allColorings(n, k):
   return itertools.product(range(k),repeat=n)

def anyColoring(n,k):
   return tuple(random.choice(range(k)) for _ in range(n))

def vertexNeighbors(c,i,k):
   newColors = set(range(k)) - set([c[i]])
   return (tuple(newColor if index == i else color for (index,color) in enumerate(c))
                        for newColor in newColors)

def neighboringColorings(c, k):
   return (x for i in range(len(c)) for x in vertexNeighbors(c, i, k))



@memoize
def hasProperColoring(g, k):
   # extend this to return the coloring
   ((n, _), edgeList) = g
   for coloring in allColorings(n, k):
      if properColoring(edgeList, coloring):
         return True
   return False


def allEdges(n):
   return ((i,j) for i in range(n) for j in range(n) if i < j)


def sortEdges(edgeList):
   return tuple(tuple(sorted(e)) for e in edgeList)


def isResilient(g, resilience, k):
   # extend this to use any valid coloring to try to remove as many of the
   # undecided edge sets as possible (rather than start over to try to find a
   # new coloring). In this way we never need to inspect a coloring more than
   # once and so we can maintain two iterators, one for the colorings and one
   # for the edge sets
   (n,m), edgeList = g
   count = 0
   edges = sortEdges(edgeList)

   for newEdges in itertools.combinations(set(allEdges(n)) - set(edges), resilience):
      #print(newEdges)
      newGraph = ((n, m + len(newEdges)), edges + newEdges)
      if not hasProperColoring(newGraph, k):
         return False
      count += 1
      if count % 1000 == 0:
         print(count)

   return True


def tryProveResilience(g, resilience, k, leftVertices=[], rightVertices=[]):
   (n,m), edgeList = g
   count = 0
   edges = sortEdges(edgeList)
   print(edges)
   neighbors = lambda c: neighboringColorings(c,k)
   numSteps = 10000

   if leftVertices == []:
      edgeSet = itertools.combinations(set(allEdges(n)) - set(edges), resilience)
   else: # "bipartite" edges
      edgeSet = itertools.combinations([(i,j) for i in leftVertices for j in rightVertices if i != j], resilience)

   for newEdges in edgeSet:
      newGraph = ((n, m + len(newEdges)), tuple(edges) + newEdges)
      fitness = lambda c: -numBadEdges(newGraph[1], c)

      numAttempts = 0
      while fitness(localMaximum(anyColoring(n, k), fitness, neighbors, numSteps)) != 0:
         numAttempts += 1
         if numAttempts > 20000:
            print(newEdges)
            return False

      count += 1
      if count % 10000 == 0:
         print(count)

   return True


def resilienceProfile(graphs, k, resilienceCap=4):
   # continue computing with only those graphs who passed 1-resilience
   counts = []
   goodGraphs = graphs

   for i in range(1, 1 + resilienceCap):
      goodGraphs = [g for g in goodGraphs if isResilient(g, i, k)]
      counts.append(len(goodGraphs))

   return counts


def analyze(filename, maxk=6):
   graphs = getGraphs(filename)

   '''
   kColorableGraphs = [g for g in graphs if hasProperColoring(g, k)]
   percentageColorable = len(kColorableGraphs) * 100.0 / len(graphs)
   print("%G%% (%d/%d) %d-colorable" % (percentageColorable,
         len(kColorableGraphs), len(graphs), k))
   '''

   print("Percentage of k-colorable graphs which are n-resilient".center(40))
   print(filename)
   print("")

   print('k\\n' + ''.join([("%d" % i).rjust(8) for i in range(1,5)]))
   print('  ' + "-"*40)


   for k in range(3, maxk+1):
      kColorableGraphs = [g for g in graphs if hasProperColoring(g, k)]
      # print('%d %d-colorable graphs' % (len(kColorableGraphs), k))
      counts = resilienceProfile(kColorableGraphs, k)

      row = [c * 100.0 / len(kColorableGraphs) for c in counts]
      print(str(k) + '   ' + ''.join([("%.1f" % x).rjust(8) for x in row]))

   print("")


def combineGraphs(G, H):
   gDim, gEdges = G
   hDim, hEdges = H
   offset = gDim[0]

   leftVertices = range(gDim[0])
   rightVertices = range(offset + 1, offset + hDim[0])

   combinedGraph = ((gDim[0] + hDim[0], gDim[1] + hDim[1]),
                   gEdges + tuple((i + offset, j + offset) for (i,j) in hEdges))
   return combinedGraph, leftVertices, rightVertices


def checkInterEdgeResilience(G, H, resilience, k):
   unionGraph, gVertices, hVertices = combineGraphs(G, H)
   return tryProveResilience(unionGraph, resilience, k, leftVertices=gVertices,
                             rightVertices=hVertices)



if __name__ == "__main__":
   pass
   analyze(parameters.filename, maxk=parameters.tableMaxK)

   '''
   for filename in ['graph6.txt', 'graph7.txt', 'graph8.txt']:#, 'graph9.txt']:
      analyze('data/' + filename, maxk=3)
   '''

   # graphs are ((n, m), (e1, e2, ...))

   petersen = ((10,15), ((0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7),
               (7,8), (8,0), (0,9), (3,9), (6,9), (2,7), (4,8), (5,1)))


   durer = ((12,18), ((1,2), (2,3), (3,4), (4,5), (5,6), (6,1), (1,7), (2,8),
         (3,9), (4,10), (5,11), (6,0), (8,10), (8,0), (9,7), (9,11), (10,0), (11,7)))


   grotzsch = ((11,20), ((1,3), (1,5), (1,7), (1,9), (1,0), (2,3), (3,4),
         (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,0), (2,0), (2,6), (2,8), (4,8),
         (4,10), (6,10)))


   chvatal = ((12,24), ((1,2), (2,3), (3,4), (1,4), (1,5), (1,6), (2,7), (2,8),
         (3,9), (3,10), (4,11), (4,0), (5,0), (5,9), (5,10), (6,7), (6,9), (6,10),
         (7,0), (7,11), (8,0), (8,11), (8,9), (10,11)))

   k33 = ((15,18), ((0,1), (0,2), (0,3), (1,4), (2,5), (3,6), (4,7), (4,11),
                    (5,8), (5,12), (6,9), (6,13), (7,10), (8,10), (9,10),
                     (11, 14), (12,14), (13,14)))


   print(isResilient(k33, 2, 3))
   #print(tryProveResilience(petersen, 2, 3))
   #print(tryProveResilience(durer, 4, 4))
   #print(tryProveResilience(grotzsch, 4, 4))
   #print(tryProveResilience(chvatal, 3, 4))

   negationGadget = ((15,25),
         ((0,1),(0,3),(0,12),(1,2),(1,10),(2,4),(2,13),(3,4),(3,5),(4,5),(5,6),
          (6,7),(6,8),(7,8),(7,9),(8,11),(9,10),(9,12),(10,11),(11,13),(12,13),
            (0,14), (2,14), (9,14), (11,14)))


   clauseGadget = ((31,44),
         ((1,13),(2,13),(3,14),(4,14),(5,15),(6,15),(7,16),(8,16),
         (9,17),(10,17),(11,18),(12,18),(13,19),(14,20),(15,21),(16,22),(17,23),(18,24),
         (19,20),(19,25),(20,25),(21,26),(21,22),(22,26),(23,24),(23,27),(24,27),(25,28),
         (27,0),(29,0),(28,29),(28,0),(1,30),(2,30),(3,30),(4,30),(5,30),(6,30),
         (7,30),(8,30),(9,30),(10,30),(11,30),(12,30)))


   negationClauseDisconnected = ((46,69),
         ((1,13),(2,13),(3,14),(4,14),(5,15),(6,15),(7,16),(8,16),
         (9,17),(10,17),(11,18),(12,18),(13,19),(14,20),(15,21),(16,22),(17,23),(18,24),
         (19,20),(19,25),(20,25),(21,26),(21,22),(22,26),(23,24),(23,27),(24,27),(25,28),
         (27,0),(29,0),(28,29),(28,0),(1,30),(2,30),(3,30),(4,30),(5,30),(6,30),
         (7,30),(8,30),(9,30),(10,30),(11,30),(12,30),
           (31,32),(31,34),(31,43),(32,33),(32,41),(33,35),(33,44),(34,35),
           (34,36),(35,36),(36,37),(37,38),(37,39),(38,39),(38,40),(39,42),
           (40,41),(40,43),(41,42),(42,44),(43,44),(31,45),(33,45),(40,45),(42,45)))

   negationClauseConnected = ((45,69),
         ((1,13),(2,13),(3,14),(4,14),(5,15),(6,15),(7,16),(8,16),
         (9,17),(10,17),(11,18),(12,18),(13,19),(14,20),(15,21),(16,22),(17,23),(18,24),
         (19,20),(19,25),(20,25),(21,26),(21,22),(22,26),(23,24),(23,27),(24,27),(25,28),
         (27,0),(29,0),(28,29),(28,0),(1,30),(2,30),(3,30),(4,30),(5,30),(6,30),
         (7,30),(8,30),(9,30),(10,30),(11,30),(12,30),
           (1,31),(1,33),(1,42),(31,2),(31,40),(2,34),(2,43),(33,34),
           (33,35),(34,35),(35,36),(36,37),(36,38),(37,38),(37,39),(38,41),
           (39,40),(39,42),(40,41),(41,43),(42,43),(1,44),(2,44),(39,44),(41,44)))

   clauseClauseDisconnected = ((61, 88), ((1, 13), (2, 13), (3, 14), (4, 14), (5,
      15), (6, 15), (7, 16), (8, 16), (9, 17), (10, 17), (11, 18), (12, 18), (13, 19), (14,
      20), (15, 21), (16, 22), (17, 23), (18, 24), (19, 20), (19, 25), (20, 25), (21, 26),
      (21, 22), (22, 26), (23, 24), (23, 27), (24, 27), (25, 28), (27, 0), (29, 0), (28,
      29), (28, 0), (1, 30), (2, 30), (3, 30), (4, 30), (5, 30), (6, 30), (7, 30), (8, 30),
      (9, 30), (10, 30), (11, 30), (12, 30),

         (32, 44), (33, 44), (34, 45), (35, 45), (36, 46), (37, 46), (38, 47), (39, 47),
      (40, 48), (41, 48), (42, 49), (43, 49), (44, 50), (45, 51), (46, 52), (47, 53), (48,
      54), (49, 55), (50, 51), (50, 56), (51, 56), (52, 57), (52, 53), (53, 57), (54, 55),
      (54, 58), (55, 58), (56, 59), (58, 31), (60, 31), (59, 60), (59, 31), (32, 30), (33,
      30), (34, 30), (35, 30), (36, 30), (37, 30), (38, 30), (39, 30), (40, 30), (41, 30),
      (42, 30), (43, 30)))


   clauseClauseConnected = ((61, 88), ((1, 13), (2, 13), (3, 14), (4, 14), (5, 15),
      (6, 15), (7, 16), (8, 16), (9, 17), (10, 17), (11, 18), (12, 18), (13, 19), (14, 20),
      (15, 21), (16, 22), (17, 23), (18, 24), (19, 20), (19, 25), (20, 25), (21, 26), (21,
      22), (22, 26), (23, 24), (23, 27), (24, 27), (25, 28), (27, 0), (29, 0), (28, 29),
      (28, 0), (1, 30), (2, 30), (3, 30), (4, 30), (5, 30), (6, 30), (7, 30), (8, 30), (9,
      30), (10, 30), (11, 30), (12, 30),

      (1, 44), (2, 44), (34, 45), (35, 45), (36, 46), (37, 46), (38, 47), (39, 47), (40,
      48), (41, 48), (42, 49), (43, 49), (44, 50), (45, 51), (46, 52), (47, 53), (48, 54),
      (49, 55), (50, 51), (50, 56), (51, 56), (52, 57), (52, 53), (53, 57), (54, 55), (54,
      58), (55, 58), (56, 59), (58, 31), (60, 31), (59, 60), (59, 31), (1, 30), (2, 30),
      (34, 30), (35, 30), (36, 30), (37, 30), (38, 30), (39, 30), (40, 30), (41, 30), (42,
      30), (43, 30)))


   # print(tryProveResilience(negationGadget, 1, 3))
   # print(tryProveResilience(clauseGadget, 1, 3))
   # print(tryProveResilience(negationClauseDisconnected, 1, 3, leftVertices=range(31), rightVertices=range(31,46)))
   # print(tryProveResilience(negationClauseConnected, 1, 3, leftVertices=range(31), rightVertices=[1,2] + range(31,45)))
   # print(tryProveResilience(clauseClauseConnected, 1, 3, leftVertices=range(31), rightVertices=[1,2] + range(31,61)))
   # print(tryProveResilience(clauseClauseDisconnected, 1, 3, leftVertices=range(31), rightVertices=range(31,61)))
   # works!



