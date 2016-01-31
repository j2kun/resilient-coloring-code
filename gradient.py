# localMax: 'a, ('a -> number), 'a -> ['a], int -> 'a
def localMaximum(posn, fitness, neighbors, numSteps):
   value = fitness(posn)
   nbrs = iter(neighbors(posn))

   for step in range(numSteps):

      try:
         nextPosn = nbrs.next()
      except:
         break

      nextValue = fitness(nextPosn)

      if nextValue > value:
         posn, value = nextPosn, nextValue
         nbrs = iter(neighbors(posn))

   return posn
