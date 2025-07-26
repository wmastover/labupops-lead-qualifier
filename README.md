# LabUpOps Lead Qualifier

An AI-powered website audit tool that uses GPT-4o Vision to analyze website screenshots and determine if they appear outdated or modern. This helps qualify leads by identifying potential clients with websites that may need updating.

## 🎯 Features

- **Visual AI Analysis**: Uses OpenAI's GPT-4o Vision model to analyze website aesthetics
- **Automated Screenshots**: Captures full-page screenshots using Playwright
- **Batch Processing**: Process multiple URLs from CSV files
- **Detailed Reports**: Generates CSV reports with judgment, confidence scores, and explanations
- **Modern Detection**: Identifies outdated design patterns, typography, layouts, and UX elements

## 📋 Requirements

- Python 3.8+
- OpenAI API key with GPT-4o access
- Internet connection for website screenshots and API calls

## 🚀 Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/wmastover/labupops-lead-qualifier.git
   cd labupops-lead-qualifier
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Run the lead qualifier**:
   ```bash
   cd "2. Lead qualifier"
   python lead_qualifier.py
   ```

## 📁 Project Structure

```
LabUpOps/
├── 1. Places API lead scraper/     # Lead scraping tools
├── 2. Lead qualifier/              # AI website audit tool
│   ├── lead_qualifier.py          # Main script
│   ├── sample_urls.csv           # Sample URLs for testing
│   └── audit_results.csv         # Generated results (after running)
├── requirements.txt               # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🔧 Usage

### Basic Usage

The script will automatically look for `sample_urls.csv` in the lead qualifier folder. If found, it will process those URLs; otherwise, it will use built-in sample URLs.

```bash
python lead_qualifier.py
```

### Custom URL File

To process your own URLs, create a CSV file with a `url` column:

```csv
url
example.com
your-client-site.com
another-site.com
```

Update the `urls_file` path in the `main()` function or modify the script to accept command-line arguments.

### Programmatic Usage

```python
from lead_qualifier import LeadQualifier

# Initialize
qualifier = LeadQualifier()

# Process URLs
urls = ["example.com", "old-site.com"]
results = await qualifier.process_urls(urls, "results.csv")

# Check results
for result in results:
    print(f"{result['url']}: {result['judgment']} ({result['confidence']}%)")
```

## 📊 Output Format

The tool generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `url` | The analyzed website URL |
| `judgment` | `Modern`, `Outdated`, or `Unclear` |
| `confidence` | Confidence score from 0-100 |
| `reason` | 1-2 sentence explanation |
| `screenshot_taken` | Whether screenshot was successful |
| `timestamp` | When the analysis was performed |

## 🧠 AI Analysis Criteria

The GPT-4o model evaluates websites based on:

- **Layout Design**: Responsive vs fixed-width, modern grid systems
- **Typography**: Modern font choices vs default system fonts
- **Color Schemes**: Contemporary color palettes and visual hierarchy
- **Navigation**: Modern navigation patterns and UI elements
- **Visual Sophistication**: Overall design quality and current trends
- **Mobile-First Design**: Responsive design principles
- **White Space**: Effective use of spacing and content density

## ⚙️ Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Script Configuration

You can modify these settings in the `LeadQualifier` class:

```python
self.screenshot_width = 1920      # Screenshot width
self.screenshot_height = 1080     # Screenshot height  
self.timeout = 30000             # Page load timeout (ms)
```

## 🔍 Lead Qualification Workflow

1. **Input**: Website URLs from your lead list
2. **Screenshot**: Automated full-page screenshots
3. **AI Analysis**: GPT-4o evaluates design modernity
4. **Scoring**: Confidence-based qualification scores
5. **Output**: Prioritized lead list based on website quality

## 🚨 Common Issues

### API Rate Limits
- The script includes 1-second delays between requests
- For large batches, consider implementing exponential backoff

### Screenshot Failures
- Some sites block automated screenshots
- Check for CAPTCHA or bot protection
- Verify URL accessibility

### API Costs
- GPT-4o Vision API calls cost approximately $0.01-0.02 per image
- Monitor usage for large-scale processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the LabUpOps lead generation toolkit.

## 🆘 Support

For issues and questions:
- Check the [Issues](https://github.com/wmastover/labupops-lead-qualifier/issues) page
- Review common troubleshooting steps above
- Contact the development team

---

**Note**: This tool requires an OpenAI API key and will incur API usage costs. Monitor your usage and set appropriate billing limits. 