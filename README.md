# 🔹 GitHub PR/Issue Fetcher

An interactive web application to fetch and display GitHub Pull Requests or Issues with a clean, professional interface.

## Features

✅ **Repository URL Validation** - Validates GitHub repository URLs with proper format checking  
✅ **Data Type Selection** - Choose between Pull Requests or Issues  
✅ **Dynamic List Population** - Fetches and displays items from GitHub API  
✅ **Detailed View** - Shows comprehensive information including:
- Title and Author with avatar
- Status (open/closed/merged) with color coding
- Created and Updated dates
- Labels (for Issues) with color-coded tags
- Full description/body content
- Direct link to GitHub

✅ **Error Handling** - User-friendly error messages and validation  
✅ **Rate Limiting Protection** - Prevents API abuse  
✅ **Responsive Design** - Works on desktop and mobile devices  
✅ **Professional UI** - Clean, modern interface with smooth animations

## How to Use

1. **Enter Repository URL**: Input a GitHub repository URL in the format `https://github.com/user/repo`
2. **Validate**: Click the "Validate" button to verify the URL format
3. **Select Data Type**: Choose either "Pull Requests" or "Issues" from the dropdown
4. **Browse Items**: Select any item from the populated list to view details
5. **View Details**: See comprehensive information about the selected PR/Issue

## Demo

The application includes demo data for `microsoft/vscode` to showcase functionality when GitHub API access is limited (due to CORS restrictions in local development).

## Setup

### Local Development

1. **Clone the repository**
2. **Start a local HTTP server**:
   ```bash
   # Using Python 3
   python3 -m http.server 8000
   
   # Using Python 2
   python -m SimpleHTTPServer 8000
   
   # Using Node.js (if you have npx)
   npx serve .
   ```
3. **Open in browser**: Navigate to `http://localhost:8000`

### Production Deployment

For production use, deploy to any static hosting service:
- GitHub Pages
- Netlify
- Vercel
- Any web server

**Note**: For production use with real GitHub API access, you may need to:
- Set up a backend proxy to handle CORS
- Add GitHub API authentication for higher rate limits
- Implement proper error handling for different API responses

## File Structure

```
├── index.html      # Main HTML structure
├── style.css       # CSS styling and responsive design
├── script.js       # Core JavaScript functionality
├── demo.js         # Demo mode with mock data
└── README.md       # This documentation
```

## Technical Details

- **Pure HTML/CSS/JavaScript** - No frameworks required
- **GitHub API Integration** - Uses REST API v3
- **Responsive Design** - Mobile-friendly interface
- **Modern Browser Support** - ES6+ features used
- **Accessibility** - Proper ARIA labels and semantic HTML

## API Usage

The application makes requests to:
- `GET /repos/{owner}/{repo}/pulls` - For Pull Requests
- `GET /repos/{owner}/{repo}/issues` - For Issues

Rate limiting is handled gracefully with user feedback.

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## License

MIT License - Feel free to use and modify as needed.