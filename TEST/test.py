import random
import collections

class ColorManager():
    def __init__(self):
        self._colorSets = collections.defaultdict()
        self.RANDOM_COLOR = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def listColorSets(self):
        return list(self._colorSets.keys())

    def getColorSet(self, name):
        try : return self._colorSets[str(name)]
        except: return [self.RANDOM_COLOR()]

    def setRandomColorSet(self, name, q):
        if q>0: self._colorSets[str(name)] = [self.RANDOM_COLOR() for _ in range(q)]

    def setColorSet(self, name, arr: list):
        """ Color array must like that: [(255, 255, 255), (0, 0, 0), (120, 150, 180)...]"""
        self._colorSets[str(name)] = arr

    def deleteColorSet(self, name):
        try: self._colorSets.pop(name)
        except: pass


cm = ColorManager()
cm.setRandomColorSet("AOS_1", 10)
print(cm.getColorSet("AOS_1"))