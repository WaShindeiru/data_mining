import pandas as pd
import json

from shapely.geometry import Point, Polygon

class Square:
  def __init__(self, points):
    self.points = points
    self.polygon = Polygon(points)
    self.values = []
    self.median = 0
    self.count = 0
    self.color = ""

if __name__ == "__main__":
  label = "attr_index_norm"

  paris_weekdays = pd.read_csv('./data/paris_weekdays.csv')
  paris_weekends = pd.read_csv('./data/paris_weekends.csv')

  paris_weekdays['is_weekend'] = False
  paris_weekends['is_weekend'] = True

  paris_all = pd.concat([paris_weekdays, paris_weekends], ignore_index=True)

  # Q_low = paris_all[label].quantile(0.015)
  # Q_high = paris_all[label].quantile(0.85)
  # paris_all = paris_all[(paris_all[label] >= Q_low) & (paris_all[label] <= Q_high)]

  # Find coordinate bounds
  print(f"Latitude  - Min: {paris_all['lat'].min()}, Max: {paris_all['lat'].max()}")
  print(f"Longitude - Min: {paris_all['lng'].min()}, Max: {paris_all['lng'].max()}")

  print((paris_all['lat'].max() - paris_all['lat'].min()) / 0.0075)
  print((paris_all['lng'].max() - paris_all['lng'].min()) / 0.0075)

  squares = []

  lat_min = paris_all['lat'].min()
  lat_max = paris_all['lat'].max()

  lng_min = paris_all['lng'].min()
  lng_max = paris_all['lng'].max()

  distance_lat = 0.005
  distance_lng = 0.0075

  padding = 0.0001

  lats_ = []
  lat_ = lat_min
  while lat_ < lat_max:
    lats_.append(lat_)
    lat_ = lat_ + distance_lat

  lngs_ = []
  lng_ = lng_min
  while lng_ < lng_max:
    lngs_.append(lng_)
    lng_ += distance_lng

  for lat in lats_:
    for lng in lngs_:
      points_ = []
      points_.append((lng, lat))
      points_.append((lng + distance_lng - padding, lat))
      points_.append((lng + distance_lng - padding, lat + distance_lat - padding))
      points_.append((lng, lat + distance_lat - padding))

      squares.append(Square(points_))

  for _, row in paris_all.iterrows():
    lat = row['lat']
    lng = row['lng']

    point_ = Point((lng, lat))

    for square in squares:
      if square.polygon.contains(point_):
        square.count += 1
        square.values.append(row[label])
        break

  import statistics
  for square in squares:
    if square.count > 0:
      square.median = statistics.median(square.values)

  medians = [d.median for d in squares if d.count > 0]
  min_median = min(medians)
  max_median = max(medians)

  for square in squares:
    if square.count > 0:
      normalized = (square.median - min_median) / (max_median - min_median)
      # #fce5a8 for low values (orange/yellow), #6b0000 for high values
      red_value = int(252 - normalized * (252 - 107))  # 252 -> 107
      green_value = int(229 - normalized * 229)  # 229 -> 0
      blue_value = int(168 - normalized * 168)  # 168 -> 0
      square.color = f"#{red_value:02X}{green_value:02X}{blue_value:02X}"
    else:
      square.color = f"#000000"

  shapes = []
  for square in squares:
    if square.count > 0:
      coordinates = []
      for point in square.points:
        coordinates.append({
          "lat": point[1],
          "lng": point[0],
        })

      shapes.append({
        "coordinates": coordinates,
        "color": square.color,
        "value": square.median,
      })

  output = {"shapes": shapes, "label": label}

  with open('./data/heatmap.json', 'w') as f:
    json.dump(output, f, indent=2)

  print("Saved heatmap.json")