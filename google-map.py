import pandas as pd
import json

class DistrictData:
  def __init__(self, id):
    self.prices = []
    self.id = id
    self.mean = 0
    self.color = ""

if __name__ == "__main__":
  districts = {i: DistrictData(i) for i in range(1, 21, 1)}

  # Read weekdays and weekends CSV files
  paris_weekdays = pd.read_csv('./data/paris_weekdays_district.csv')
  paris_weekends = pd.read_csv('./data/paris_weekends_district.csv')

  # Add weekend flag and merge
  paris_weekdays['is_weekend'] = False
  paris_weekends['is_weekend'] = True

  paris_all = pd.concat([paris_weekdays, paris_weekends], ignore_index=True)

  # Read districts.json
  with open('./data/districts.json', 'r') as f:
    districts_json = json.load(f)

  # Iterate over paris_all and add realSum to corresponding DistrictData
  for _, row in paris_all.iterrows():
    district_id = int(row['district'])
    if district_id in districts:
      districts[district_id].prices.append(row['realSum'])

  for district_id, district_data in districts.items():
    if district_data.prices:
      district_data.mean = sum(district_data.prices) / len(district_data.prices)

  # Find smallest and biggest mean
  means = [d.mean for d in districts.values() if d.mean > 0]
  min_mean = min(means)
  max_mean = max(means)

  # Assign colors based on mean (0F to FF for red channel)
  for district_id, district_data in districts.items():
    if district_data.mean > 0:
      # Normalize mean to 0-1 range
      normalized = (district_data.mean - min_mean) / (max_mean - min_mean)
      # Map to color range 0F (15) to FF (255)
      red_value = int(15 + normalized * (255 - 15))
      district_data.color = f"#{red_value:02X}0000"

  # Create JSON structure with shapes
  shapes = []
  for district in districts_json:
    district_id = district['district_id']
    if district_id in districts:
      coordinates = []
      for point in district['points']:
        coordinates.append({
          "lat": point[1],  # latitude is second element
          "lng": point[0]   # longitude is first element
        })
      shapes.append({
        "coordinates": coordinates,
        "color": districts[district_id].color
      })

  output = {"shapes": shapes}

  # Save to JSON file
  with open('./data/districts_colored.json', 'w') as f:
    json.dump(output, f, indent=2)

  print("Saved districts_colored.json")



