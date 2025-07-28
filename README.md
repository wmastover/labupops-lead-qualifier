# LabUpOps Lead Qualifier

An AI-powered website audit tool that uses GPT-4o Vision to analyze website screenshots and determine if they appear outdated or modern. This helps qualify leads by identifying potential clients with websites that may need updating.

## 🎯 Features

- **Visual AI Analysis**: Uses OpenAI's GPT-4o Vision model to analyze website aesthetics
- **Automated Screenshots**: Captures full-page screenshots using Playwright
- **AI Logo Detection**: Automatically finds and validates website logos using computer vision
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

5. **Run the scripts**:
   ```bash
   # Website quality assessment
   python3 "3. lead_qualifier.py"
   
   # Logo detection and validation
   python3 "5. lead_logo.py"
   ```

## 📁 Project Structure

```
LabUpOps/
├── 1. lead_scraper.py             # Google Places API lead scraper
├── 2. lead_filter.py              # Lead filtering and validation
├── 3. lead_qualifier.py           # AI website quality assessment
├── 4. lead_email_finder.py        # Email contact discovery
├── 5. lead_logo.py                # AI-powered logo detection ← NEW!
├── lead_lists/                    # Generated lead data
│   ├── *.csv                     # Lead CSV files
│   └── *_logos.csv               # Logo analysis results
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── LOGO_FINDER_README.md         # Logo finder documentation
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

## 🔍 Complete Lead Generation Workflow

1. **Lead Scraping** (`1. lead_scraper.py`): Extract businesses from Google Places API
2. **Lead Filtering** (`2. lead_filter.py`): Validate and clean lead data
3. **Website Qualification** (`3. lead_qualifier.py`): AI analysis of website design quality
4. **Logo Detection** (`5. lead_logo.py`): Find and validate business logos using AI Vision
5. **Email Discovery** (`4. lead_email_finder.py`): Find contact email addresses

### Logo Detection Workflow
1. **Input**: Qualified leads with website URLs
2. **Logo Scanning**: Automated detection of potential logo images using CSS selectors
3. **AI Validation**: GPT-4o Vision API verifies images are actual business logos
4. **Quality Assessment**: Evaluates logo quality and business name presence
5. **Output**: Logo URLs with confidence scores and detailed analysis

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