# 🎨 Background Generator

An AI-powered tool that creates stunning landscape website backgrounds based on company logos using OpenAI's DALL-E 3 and GPT-4 Vision models.

## 🌟 Features

- **Intelligent Logo Analysis**: Uses GPT-4 Vision to analyze logo colors, style, industry, and brand personality
- **Context-Aware Generation**: Creates backgrounds that complement the company's brand and industry
- **Batch Processing**: Process multiple logos from CSV files
- **High-Quality Output**: Generates 1792x1024 HD landscape images perfect for website backgrounds
- **Flexible Input**: Supports both local files and URLs for logos
- **Detailed Reporting**: Saves comprehensive results including analysis data and generation prompts

## 🎯 How It Works

1. **Logo Analysis**: GPT-4 Vision analyzes the company logo to extract:
   - Primary and secondary colors
   - Design style (modern, classic, minimalist, etc.)
   - Industry type
   - Brand personality
   - Visual elements

2. **Prompt Generation**: Creates intelligent DALL-E prompts based on:
   - Logo analysis results
   - Company description
   - Industry-specific aesthetics
   - Style preferences

3. **Background Creation**: Uses DALL-E 3 to generate:
   - Wide landscape format (16:9 ratio)
   - High-definition quality
   - Complementary color schemes
   - Professional composition suitable for text overlay

## 📋 Requirements

- Python 3.8+
- OpenAI API key with DALL-E 3 and GPT-4 Vision access
- Internet connection for API calls and URL-based logos

## 🚀 Installation

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## 💡 Usage

### Command Line Interface

#### Single Logo Processing
```bash
python background_generator.py --logo "path/to/logo.png" --name "Company Name" --description "Brief company description" --style "modern and clean"
```

#### Using URL for Logo
```bash
python background_generator.py --logo "https://logo.clearbit.com/apple.com" --name "Apple" --description "Consumer electronics company"
```

#### Batch Processing from CSV
```bash
python background_generator.py --csv "logos.csv"
```

#### Generate Without Saving Locally
```bash
python background_generator.py --logo "logo.png" --no-save
```

### Command Line Arguments

- `--logo, -l`: Path or URL to company logo (required for single processing)
- `--name, -n`: Company name
- `--description, -d`: Company description to influence background style
- `--style, -s`: Style preference (e.g., "modern minimalist", "bold and dynamic")
- `--csv, -c`: CSV file for batch processing
- `--no-save`: Don't save images locally (only return URLs)
- `--api-key`: OpenAI API key (overrides environment variable)

### Programmatic Usage

```python
from background_generator import BackgroundGenerator

# Initialize generator
generator = BackgroundGenerator()

# Process single logo
result = generator.process_single_logo(
    logo_path="https://logo.clearbit.com/company.com",
    company_name="Company Name",
    company_description="What the company does",
    style_preference="modern and professional"
)

print(f"Generated image URL: {result['image_url']}")
```

## 📊 CSV Batch Processing Format

Create a CSV file with the following columns:

```csv
logo_path,company_name,company_description,style_preference
https://logo.clearbit.com/apple.com,Apple,"Consumer electronics company",modern minimalist
path/to/local/logo.png,Local Company,"Software development",clean and innovative
```

**Required columns:**
- `logo_path`: Path to logo file or URL

**Optional columns:**
- `company_name`: Company name
- `company_description`: Brief description of what the company does
- `style_preference`: Desired aesthetic style

## 🎨 Industry-Specific Styles

The generator automatically adapts backgrounds based on detected industry:

- **Technology**: Futuristic cityscapes with clean lines and digital elements
- **Healthcare**: Serene natural landscapes with soft, calming elements
- **Finance**: Modern urban skylines with geometric patterns
- **Education**: Inspiring mountain or forest vistas with bright, optimistic tones
- **Retail**: Vibrant, energetic landscapes with dynamic elements
- **Consulting**: Professional, clean landscapes with subtle sophistication
- **Creative**: Artistic, imaginative landscapes with bold visual interest
- **Manufacturing**: Industrial-inspired landscapes with strong, reliable elements

## 📁 Output

### Generated Files

- **Images**: Saved to `generated_backgrounds/` directory
- **Results CSV**: Comprehensive report with analysis and generation data
- **Naming**: `{company_name}_{timestamp}.png`

### Result Data

Each generation includes:
- Original logo analysis (colors, style, industry, personality)
- Generated DALL-E prompt
- Revised prompt (as modified by DALL-E)
- Image URL
- Local file path (if saved)
- Timestamp
- Error information (if any)

## 🔧 Customization

### Image Settings

Modify these class attributes in `BackgroundGenerator`:

```python
self.image_size = "1792x1024"  # Wide landscape format
self.quality = "hd"            # "standard" or "hd"
self.style = "natural"         # "natural" or "vivid"
```

### Style Preferences

Use descriptive style preferences for better results:
- "modern minimalist with clean lines"
- "bold and dynamic with vibrant colors"
- "professional and trustworthy"
- "creative and artistic"
- "warm and welcoming"
- "high-tech and futuristic"

## 🚨 Error Handling

The generator includes robust error handling:
- **Logo Analysis Failures**: Falls back to default analysis
- **Network Issues**: Retries and informative error messages
- **API Errors**: Detailed error reporting
- **File Issues**: Graceful handling of missing files or invalid URLs

## 💰 Cost Considerations

- **GPT-4 Vision**: ~$0.01-0.02 per logo analysis
- **DALL-E 3**: ~$0.04-0.08 per image generation (depending on quality)
- **Batch Processing**: Consider API rate limits and costs for large batches

## 📝 Examples

See `example_usage.py` for detailed programmatic examples:

```bash
python example_usage.py
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure `OPENAI_API_KEY` is set correctly
   - Verify API key has access to GPT-4 Vision and DALL-E 3

2. **Logo Analysis Fails**
   - Check logo URL is accessible
   - Ensure logo file exists and is readable
   - Try different image formats (PNG, JPG, JPEG)

3. **Generation Quality Issues**
   - Provide more detailed company descriptions
   - Use specific style preferences
   - Check logo image quality and clarity

4. **File Saving Issues**
   - Ensure write permissions in output directory
   - Check available disk space
   - Verify network connection for URL downloads

### Debug Mode

For more detailed output, check the console logs during processing. The generator provides extensive logging for each step.

## 🤝 Integration

The background generator can be easily integrated into existing workflows:

- **Lead Qualification Pipeline**: Generate backgrounds for prospect companies
- **Web Design Automation**: Create custom backgrounds for client websites
- **Marketing Tools**: Generate branded backgrounds for campaigns
- **CMS Integration**: Automatically create backgrounds based on company data

## 📄 License

This tool is part of the LabUpOps Lead Qualifier project. See the main README for license information.