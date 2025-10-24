Task: Implement a frontend web application called "World Clock Map" with the following features:

Requirements:

1. Map Interaction:
   - Display an interactive world map using Leaflet.js or Google Maps API.
   - Predefine a list of major cities with their coordinates and timezones (e.g., New York, London, Tokyo, Sydney).
   - Clicking a city marker on the map adds that city to a "World Clock List".
   - Hovering over a marker shows the city name and timezone.

2. World Clock List:
   - Display all added cities with:
     * City name
     * Local time (updated every second)
     * Timezone
   - Allow users to remove cities from the list.
   - Optional: Allow users to drag and reorder cities in the list.

3. Time Calculation:
   - Use the city's timezone to calculate local time accurately.
   - Time formatting should be done via JavaScript `Intl.DateTimeFormat` or libraries like Luxon or Day.js.
   - Optional: Allow switching between 12-hour and 24-hour format, and display date and weekday.

4. UI Layout:
   - Map should appear at the top of the page.
   - Clock list should appear below the map.
   - UI should be clean, simple, and responsive.

5. Data Example (predefined cities):
   [
     {"name": "New York", "lat": 40.7128, "lng": -74.0060, "timezone": "America/New_York"},
     {"name": "London", "lat": 51.5074, "lng": -0.1278, "timezone": "Europe/London"},
     {"name": "Tokyo", "lat": 35.6895, "lng": 139.6917, "timezone": "Asia/Tokyo"},
     {"name": "Sydney", "lat": -33.8688, "lng": 151.2093, "timezone": "Australia/Sydney"}
   ]

Output Requirements:
- Provide a working HTML/JS/CSS frontend application.
- Include comments explaining key code sections.
- Demonstrate at least 4 cities in the initial setup.
- Ensure local times update every second correctly.
- Clicking a city marker adds it to the list, clicking "remove" deletes it.

Optional Enhancements:
- 12/24-hour toggle
- Date and weekday display
- Drag to reorder cities
