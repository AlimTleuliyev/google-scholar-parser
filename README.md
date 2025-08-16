# Scholar Profile Parser

A tool to help graduate students research potential advisors by extracting detailed publication information from Google Scholar profiles.

## The Idea

As a new graduate student, choosing the right professor for advisorship is crucial. This tool helps you:

1. **Research professors quickly** - Get their latest papers with full abstracts
2. **Understand their work** - Extract comprehensive publication details 
3. **Chat with AI about their research** - Feed the data to ChatGPT, Claude, or Gemini to discuss their research focus, methodology, and recent directions

Instead of manually browsing through dozens of papers, get structured data you can analyze with AI assistance.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Get latest 10 papers from a researcher
python3 parser.py "Stephen Hawking"

# Get papers from 2020 onwards with faster processing
python3 parser.py "Stephen Hawking" --year-limit 2020 --num-workers 8

# Save results to JSON for AI analysis
python3 parser.py "Stephen Hawking" --output hawking_papers.json
```

## Usage Examples

```bash
# Basic usage - get 20 most recent papers
python3 parser.py "Stephen Hawking"

# Limit to recent work (2022 and newer)
python3 parser.py "Stephen Hawking" --year-limit 2022

# Get more papers with parallel processing
python3 parser.py "Stephen Hawking" --max-papers 50 --num-workers 8

# Combine max papers and year limit for focused research
python3 parser.py "Stephen Hawking" --max-papers 30 --year-limit 2015

# Save to file for AI chat
python3 parser.py "Stephen Hawking" --output hawking_papers.json --year-limit 2020
```

## Parameter Strategy & Tips

**⚠️ Important: Experiment with parameters based on the researcher's productivity**

- **High-productivity researchers**: May have 20+ papers per year
  - Use higher `--max-papers` (50-100) with `--year-limit` to avoid going too far back
  - Example: `--max-papers 50 --year-limit 2022` gets recent high-volume work

- **Selective researchers**: May have 5-10 papers per year  
  - Use longer time range: `--year-limit 2018` with default `--max-papers 20`
  - This ensures you capture sufficient work without missing important papers

- **Finding the balance**: If you set `--max-papers 10 --year-limit 2024` but the researcher published 20 papers in 2025, you'll miss their 2024 work entirely. Start broad, then narrow down.

**Recommended approach:**
1. First run: `--max-papers 30 --year-limit 2020` (get overview)
2. Adjust based on publication pattern you observe

## Options

- `--max-papers N`: Maximum number of papers to fetch (default: 20)
- `--year-limit YYYY`: Stop when reaching papers older than this year
- `--num-workers N`: Parallel workers for faster processing (default: 4)
- `--profile-index N`: Which profile to use if multiple found (default: 0)
- `--output FILE`: Save results to JSON file

## AI Integration Workflow

1. **Extract papers**: `python3 parser.py "Stephen Hawking" --output hawking_data.json`
2. **Copy the JSON output** or key abstracts
3. **Chat with AI**: Paste into ChatGPT/Claude/Gemini with prompts like:
   - "Analyze this researcher's work focus and methodology"
   - "What are the main themes in their recent research?"
   - "Is this researcher a good fit for [your research interests]?"

## Output Format

The tool extracts:
- Paper titles and full abstracts
- Author lists and publication venues
- Citation counts and publication years
- Journal details (volume, pages, publisher)
- Direct links to paper details

Perfect for understanding a researcher's expertise, recent directions, and research style before reaching out for potential advisorship.

*See `hawking_papers.json` for example output format.*

## Note

Be respectful with requests - the tool includes delays between requests to avoid overwhelming Google Scholar servers.
