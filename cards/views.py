from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import json
import os

def load_data():
    """Load the JSONL data from the file."""
    data_file_path = os.path.join(settings.BASE_DIR, 'data', 'merged_data.jsonl')
    data = []
    
    try:
        with open(data_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():
                    data.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass  # Return empty list if file not found
    
    return data

def index(request):
    """Main view for the card display page."""
    return render(request, 'cards/index.html')

def api_data(request):
    """API endpoint to serve the data as JSON."""
    data = load_data()
    return JsonResponse({'data': data, 'total': len(data)})
