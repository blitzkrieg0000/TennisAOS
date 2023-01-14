



Algorithms : dict[str, list[str]] = {
    "A" : None,
    "B" : ["A"],
    "C" : ["A"],
    "D" : ["A","C"],
    "E" : ["C"],
    "F" : None,
    "G" : ["D", "E"],
    "H" : ["A", "E"]
}


def SolveAlgorithmSequence(Algorithms):
    AlgorithmChainSequence = []
    PlacedAlgorithms = []
    UnplacedAlgorithms = Algorithms.copy()
    for key, value in Algorithms.items():
        if value is None:
            PlacedAlgorithms.append(key)
            UnplacedAlgorithms.pop(key)

    AlgorithmChainSequence.append(PlacedAlgorithms.copy())

    for _ in range(len(UnplacedAlgorithms)):
        selected = []
        for key, dependencies in UnplacedAlgorithms.items():
            if all([dependecy in PlacedAlgorithms for dependecy in dependencies]):
                selected.append(key)

        [(UnplacedAlgorithms.pop(skey), PlacedAlgorithms.append(skey)) for skey in selected]
        if len(selected) > 0:
            AlgorithmChainSequence.append(selected)

    return AlgorithmChainSequence


print(SolveAlgorithmSequence(Algorithms))








