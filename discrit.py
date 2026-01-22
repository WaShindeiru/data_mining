import json
import os
import copy
import csv

from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

def read_json_file(filename):
    try:
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found")
            return None
        
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Successfully read JSON from '{filename}'")
            return data
            
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{filename}'")
        print(f"Error details: {e}")
        return None
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        return None

def draw_district_inner(election_data, name):
    plt.figure()

    for key_, datum in election_data.items():
        geo_data = datum["geo_shape"]["geometry"]["coordinates"][0] 
        print(len(geo_data))
        longitude = [x[0] for x in geo_data]
        latitude = [x[1] for x in geo_data]
        plt.scatter(longitude, latitude, label=datum["id_bv"])

    plt.legend()
    plt.savefig(f"{name}.png")
    plt.show()

def draw_district(district_data, name):
    plt.figure()

    geo_data = district_data["points"]
    print(len(geo_data))
    longitude = [x[0] for x in geo_data]
    latitude = [x[1] for x in geo_data]
    plt.scatter(longitude, latitude, label=district_data["district_id"])

    plt.legend()
    plt.savefig(f"{name}.png")
    plt.show()


def parse_district_data(election_data):

    district_data = [{} for i in range(21)]

    for data_ in election_data:
        numbers = data_["id_bv"].split("-")
        
        first_num = int(numbers[0])
        second_num = int(numbers[1])

        try:
            district_data[first_num][second_num] = data_
        except IndexError:
            print(f"first_num: {first_num}, second_num: {second_num}")

    return district_data

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union

def connect_shapes_and_clean(shapes_points, connection_distance=None):
    polygons = []
    for points in shapes_points:
        poly = Polygon(points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        polygons.append(poly)
    
    if connection_distance is not None:
        buffered_polys = [poly.buffer(connection_distance/4) for poly in polygons]
        merged = unary_union(buffered_polys)
        merged = merged.buffer(-connection_distance/4)
    else:
        merged = unary_union(polygons)
    
    if merged.geom_type == 'Polygon':
        boundary_points = np.array(merged.exterior.coords)
    elif merged.geom_type == 'MultiPolygon':
        boundary_points = []
        for poly in merged.geoms:
            boundary_points.extend(poly.exterior.coords)
        boundary_points = np.array(boundary_points)
    else:
        boundary_points = np.array(merged.boundary.coords)
    
    return boundary_points

def remove_connections(parsed_data):
    
    result_data = [{} for i in range(21)]

    for district_num, district in enumerate(parsed_data):
        all_points = []

        for key_, smaller_disctrict in district.items():
            geo_data = smaller_disctrict["geo_shape"]["geometry"]["coordinates"][0] 

            all_points = connect_shapes_and_clean([all_points, geo_data])

        

        result_data[district_num]["district_id"] = district_num
        result_data[district_num]["points"] = all_points
    
    return result_data

def remove_inner_points(parsed_data):
    
    result_data = [{} for i in range(21)]

    for district_num, district in enumerate(parsed_data):
        all_points = []

        for key_, smaller_disctrict in district.items():
            geo_data = smaller_disctrict["geo_shape"]["geometry"]["coordinates"][0] 

            for point in geo_data:
                all_points.append(point)

        polygon = Polygon(all_points)
            
        points_outside = []
        points_inside = []

        for point in all_points:
            p = Point(point)
            if not polygon.contains(p):
                points_outside.append(point)
            else:
                points_inside.append(point)

        print(f"district id: {district_num}, num of points outisde: {len(points_outside)}")
        print(f"district id: {district_num}, num of points inside: {len(points_inside)}")

        result_data[district_num]["district_id"] = district_num
        result_data[district_num]["points"] = points_outside
    
    return result_data

def save_districts_to_csv(district_data, filename):
    """Save district data to CSV file with points as arrays, excluding index 0"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        writer.writerow(['district_id', 'points'])
        
        for district_dict in district_data[1:]:
            if district_dict and 'district_id' in district_dict:
                district_id = district_dict['district_id']
                points = district_dict['points']
                
                points_str = str(points.tolist() if hasattr(points, 'tolist') else list(points))
                writer.writerow([district_id, points_str])
    
    print(f"Successfully saved data to '{filename}'")

def assign_districts_to_csv(input_csv, output_csv, district_data):
    """Read CSV with lng/lat columns and add district column"""
    import pandas as pd
    
    df = pd.read_csv(input_csv)
    
    df['district'] = 0
    
    for idx, row in df.iterrows():
        point = Point(row['lng'], row['lat'])
        
        for district_dict in district_data[1:]:
            if district_dict and 'points' in district_dict:
                polygon = Polygon(district_dict['points'])
                
                if polygon.contains(point):
                    df.at[idx, 'district'] = district_dict['district_id']
                    break
    
    df.to_csv(output_csv, index=False)
    print(f"Successfully saved data with districts to '{output_csv}'")
    print(f"Districts assigned: {df['district'].value_counts().sort_index()}")


if __name__ == "__main__":
    election_data = read_json_file("./data/elections-europeennes-2024.json")

    parsed_data = parse_district_data(election_data)

    removed_data = remove_connections(parsed_data)

    assign_districts_to_csv("data/paris_weekdays.csv", "data/paris_weekdays_district.csv", removed_data)
    assign_districts_to_csv("data/paris_weekends.csv", "data/paris_weekends_district.csv", removed_data)