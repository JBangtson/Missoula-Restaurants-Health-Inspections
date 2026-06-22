import folium
from folium.plugins import HeatMap, MarkerCluster
import json

with open(r'F:\Projects\30 Technology Projects\01 Github - Public\missoula_restaurants\etl\extract\google_places\missoula_restaurants_complete.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Your clean data structure
restaurants = data

# Create map centered on Missoula, MT
m = folium.Map(
    location=[46.8554, -114.0001],  # Center on Missoula
    zoom_start=12,
    tiles='CartoDB positron'  # Clean, reliable tile source
)
# OpenStreetMap
# CartoDB positron
# CartoDB dark_matter
# Optional: Add a marker cluster for better organization with many markers
marker_cluster = MarkerCluster().add_to(m)

# Add markers from your list of dicts
for restaurant in restaurants:
    # Create popup HTML with better formatting
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px;">
        <h4 style="margin: 0 0 5px 0;">{restaurant['name']}</h4>
        <p style="margin: 0 0 3px 0; font-size: 12px;">{restaurant['address']}</p>
        <p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">
            <a href="https://www.google.com/maps/place/?q=place_id:{restaurant['place_id']}" 
               target="_blank">View on Google Maps</a>
        </p>
    </div>
    """
    
    # Add marker to cluster (or directly to map if you prefer)
    folium.Marker(
        location=[restaurant['latitude'], restaurant['longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=restaurant['name'],
        icon=folium.Icon(color='red', icon='cutlery', prefix='fa')  # Fork/knife icon
    ).add_to(marker_cluster)  # Change to m.add_to() if not using clusters

# Add a heatmap layer (optional)
heat_data = [[r['latitude'], r['longitude']] for r in restaurants]
HeatMap(heat_data, radius=25, blur=15).add_to(m)

# Add fullscreen button
from folium.plugins import Fullscreen
Fullscreen().add_to(m)

# Save with referrer fix for local file access
output_file = 'missoula_restaurants.html'
m.save(output_file)

# Inject referrer meta tag to prevent tile loading issues
with open(output_file, 'r', encoding='utf-8') as file:
    html_content = file.read()

html_content = html_content.replace(
    '<head>', 
    '<head>\n    <meta name="referrer" content="strict-origin-when-cross-origin" />'
)

with open(output_file, 'w', encoding='utf-8') as file:
    file.write(html_content)

print(f"Map created: {output_file}")