from libs.polygon_tools import calculate_on_plane
polygon_tool = calculate_on_plane()

def scoreTypes(key):
    switcher = {
        "aos_1_area_5" : 4,
        "aos_1_area_4" : 3,
        "aos_1_area_3" : 2,
        "aos_1_area_2" : 1,
        "aos_1_area_1" : 1,
        "aos_2_area_6" : 3,
        "aos_2_area_5" : 1,
        "aos_2_area_4" : 3,
        "aos_2_area_3" : 2,
        "aos_2_area_2" : 1,
        "aos_2_area_1" : 2,
        "aos_3_area_4" : 2,
        "aos_3_area_3" : 2,
        "aos_3_area_2" : 2,
        "aos_3_area_1" : 2,
    }
    return switcher.get(key, 0)

def get_score(polygons:dict, point):
    for i, key in enumerate(polygons.keys()):
        points = polygons[key]
        if polygon_tool.is_inside_polygon(points=points, p=point[0]):
            score = scoreTypes(key)
            return score 
    return None