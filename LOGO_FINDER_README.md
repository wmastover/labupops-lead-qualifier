# Logo Finder - AI-Powered Website Logo Detection and Validation

The Logo Finder is an intelligent tool that automatically identifies and validates website logos using computer vision and OpenAI's GPT-4o Vision API. It analyzes web pages to find potential logo images and then uses AI to determine if they are actually the website's main logo.

## 🎯 Features

- **Smart Logo Detection**: Uses advanced CSS selectors and heuristics to find potential logo images
- **AI Validation**: Employs OpenAI's GPT-4o Vision API to verify that images are actual website logos
- **Position-Based Scoring**: Prioritizes images in header areas and with logo-related attributes
- **Batch Processing**: Process multiple websites from CSV files
- **Detailed Reports**: Generates comprehensive CSV reports with confidence scores and reasoning
- **Size Filtering**: Automatically filters out very small images that are unlikely to be logos
- **Quality Assessment**: Evaluates logo quality and identifies if the logo contains business names

## 🔧 How It Works

### 1. Logo Candidate Detection
The script searches for potential logos using multiple strategies:
- **CSS Selectors**: Targets images with logo-related classes, IDs, or attributes
- **Position Analysis**: Prioritizes images in header, navigation, and brand areas
- **Size Filtering**: Excludes very small images (< 50x20 pixels)
- **Keyword Matching**: Looks for "logo", "brand", "company", etc. in image attributes

### 2. Intelligent Scoring
Each candidate is scored based on:
- **Position on page** (top of page scores higher)
- **Size appropriateness** (reasonable logo dimensions)
- **Logo-related keywords** in alt text, class names, or file paths
- **Location in HTML structure** (header/nav areas score higher)

### 3. AI Validation
For each candidate, the OpenAI Vision API analyzes:
- Whether the image appears to be a logo or brand mark
- If it contains business-identifying elements
- Professional design quality
- Appropriateness as a main brand identifier

## 📋 Requirements

- Python 3.8+
- OpenAI API key with GPT-4o Vision access
- Internet connection for web scraping and API calls

## 🚀 Setup

1. **Install dependencies** (already done if you've set up the main project):
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Set up your OpenAI API key**:
   - Get your API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)
   - Add it to the `.env` file:
     ```
     OPENAI_API_KEY=your_actual_api_key_here
     ```

## 📖 Usage

### Single Website
Test the logo finder on a single website:
```bash
python3 "5. lead_logo.py" --url "https://example.com" --name "Company Name"
```

### CSV File Processing
Process multiple websites from a CSV file:
```bash
python3 "5. lead_logo.py" --csv "lead_lists/restaurants.csv" --output "results_with_logos.csv"
```

### Auto-Discovery
Run without arguments to automatically process the most recent qualified leads:
```bash
python3 "5. lead_logo.py"
```

## 📊 Input Format

The script expects CSV files with these columns:
- `url` or `website` or `website_url`: The website URL
- `restaurant_name` or `business_name` or `name`: Business name (optional but helpful)

Example CSV format:
```csv
restaurant_name,url,address,phone_number
Joe's Pizza,https://joespizza.com,123 Main St,555-1234
Local Cafe,https://localcafe.co.uk,456 Oak Ave,555-5678
```

## 📈 Output Format

The script generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `url` | Original website URL |
| `website_name` | Business/website name |
| `logo_found` | Boolean: true if a valid logo was found |
| `logo_url` | Direct URL to the logo image |
| `logo_confidence` | AI confidence score (0-100) |
| `logo_reasoning` | AI explanation for the decision |
| `logo_type` | Type of logo (text, symbol, combination, etc.) |
| `has_business_name` | Boolean: true if logo contains readable business name |
| `logo_quality` | Quality assessment (high, medium, low) |
| `candidates_found` | Number of potential logos detected |
| `error` | Any errors encountered during processing |
| `timestamp` | When the analysis was performed |

## 🧠 AI Validation Criteria

The GPT-4o Vision model evaluates images based on:

1. **Logo Characteristics**:
   - Professional design quality
   - Appropriate for brand identification
   - Clear and readable elements

2. **Business Relevance**:
   - Contains company/business name
   - Matches the website's brand identity
   - Appears to be the main logo (not a sub-brand or icon)

3. **Technical Quality**:
   - Sufficient resolution for logo use
   - Not corrupted or distorted
   - Appropriate file format and quality

## ⚙️ Configuration

You can modify these settings in the `LogoFinder` class:

```python
# Image and browser settings
self.screenshot_width = 1920      # Browser width for page rendering
self.screenshot_height = 1080     # Browser height
self.timeout = 30000             # Page load timeout (ms)
self.max_image_size = 20 * 1024 * 1024  # Max image size (20MB)

# Logo detection selectors (add your own)
self.logo_selectors = [
    'img[alt*="logo" i]',
    'img[src*="logo" i]',
    '.logo img',
    'header img',
    # ... add more selectors
]
```

## 📊 Example Results

```csv
url,website_name,logo_found,logo_url,logo_confidence,logo_reasoning,logo_type
https://joespizza.com,Joe's Pizza,true,https://joespizza.com/logo.png,95,"High-quality logo with clear business name and professional design",combination
https://oldsite.com,Old Site,false,,0,"No suitable logo found among candidates",other
```

## 🚨 API Costs and Rate Limits

- **GPT-4o Vision API**: ~$0.01-0.02 per image analysis
- **Rate Limiting**: Built-in 1-second delays between requests
- **Batch Processing**: Saves intermediate results every 10 websites

### Cost Estimation
- 100 websites with 2 logo candidates each = ~200 API calls = ~$2-4
- The script prioritizes candidates, so most websites only need 1-2 API calls

## 🔍 Troubleshooting

### Common Issues

**No logos found**:
- Website might block automated access
- Site uses non-standard logo placement
- Logo might be in CSS background images (not detected)

**API errors**:
- Check your OpenAI API key
- Ensure you have GPT-4o Vision access
- Verify internet connection

**Browser issues**:
- Ensure Playwright Chromium is installed: `playwright install chromium`
- Some sites might require specific browser settings

### Debug Mode
For debugging, examine the intermediate results saved every 10 websites in the output CSV file.

## 🎛️ Advanced Usage

### Custom Selectors
Add domain-specific logo selectors for better detection:

```python
# Add to logo_selectors list
'.site-branding img',
'[data-logo] img',
'.masthead .logo'
```

### Quality Filtering
Adjust confidence thresholds for different use cases:

```python
# In validate_logo_with_ai method
if validation.get("confidence", 0) >= 70:  # Adjust threshold
    # Accept as valid logo
```

## 🤝 Integration with Other Scripts

The Logo Finder integrates seamlessly with the other lead generation tools:

1. **After Lead Scraping** (`1. lead_scraper.py`): Find business contacts
2. **After Lead Filtering** (`2. lead_filter.py`): Remove invalid leads  
3. **After Lead Qualification** (`3. lead_qualifier.py`): Assess website quality
4. **Logo Finding** (`5. lead_logo.py`): Find and validate logos ← You are here
5. **Email Finding** (`4. lead_email_finder.py`): Find contact emails

This creates a complete lead generation and enrichment pipeline.

## 📄 Sample Output

When you run the script, you'll see output like:

```
📂 Using default file: lead_lists/Bishops_Stortford_restaurants_qualified.csv
📊 Found 58 websites to process

🏢 Processing website: https://cafemasalatakeaway.com/

🔍 Searching for logos on https://cafemasalatakeaway.com/
📋 Found 3 logo candidates
📸 Testing candidate 1/3: https://cafemasalatakeaway.com/images/logo.png
✅ Logo found! Confidence: 95%

📊 LOGO FINDING SUMMARY
==================================================
Total websites processed: 58
Logos found: 45 (77.6%)
High confidence logos (90%+): 32
Logos with business name: 38

Logo quality breakdown:
  High: 25
  Medium: 15
  Low: 5
```

---

**Note**: This tool requires an OpenAI API key and will incur API usage costs. Monitor your usage and set appropriate billing limits.