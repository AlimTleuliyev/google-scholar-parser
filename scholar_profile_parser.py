#!/usr/bin/env python3
"""
Google Scholar Profile Parser
This script finds an author's Google Scholar profile and extracts detailed information
about all their publications including abstracts when available.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import argparse
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import threading

class ScholarProfileParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://scholar.google.com"
        self.lock = threading.Lock()  # For thread-safe operations
    
    def search_author_profiles(self, author_name):
        """Search for author profiles on Google Scholar"""
        print(f"Searching for author profiles: {author_name}")
        
        # First, search for the author using the URL format we tested
        search_url = f"{self.base_url}/scholar"
        params = {
            'hl': 'en',
            'as_sdt': '0,5',
            'q': author_name,
            'btnG': ''
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the specific "User profiles for X" section
            profiles = []
            
            # Find the table with profile information
            # Based on the HTML, look for h3 with "User profiles for" followed by a table
            profile_header = soup.find('h3', class_='gs_rt')
            if profile_header and 'User profiles for' in profile_header.get_text():
                # Find the table that follows this header
                table = profile_header.find_next_sibling('table')
                if table:
                    # Look for h4 elements with author links
                    author_links = table.find_all('h4', class_='gs_rt2')
                    
                    for h4 in author_links:
                        link = h4.find('a')
                        if link and '/citations?user=' in link.get('href', ''):
                            profile_url = urljoin(self.base_url, link['href'])
                            profile_name = link.get_text(strip=True)
                            
                            # Extract additional info (email, citations)
                            parent_div = h4.parent
                            profile_info = parent_div.get_text(strip=True) if parent_div else profile_name
                            
                            profiles.append({
                                'name': profile_name,
                                'url': profile_url,
                                'info': profile_info
                            })
            
            return profiles
            
        except Exception as e:
            print(f"Error searching for profiles: {e}")
            return []
    
    def get_profile_papers(self, profile_url, max_papers=None, year_limit=None):
        """Get all papers from a scholar profile"""
        print(f"Fetching papers from profile: {profile_url}")
        if year_limit:
            print(f"Year limit set to: {year_limit} (will stop at papers from {year_limit-1} or earlier)")
        
        # Extract user ID from URL
        parsed_url = urlparse(profile_url)
        query_params = parse_qs(parsed_url.query)
        user_id = query_params.get('user', [''])[0]
        
        if not user_id:
            print("Could not extract user ID from profile URL")
            return []
        
        # Build the URL to get the author's publications list
        papers_url = f"{self.base_url}/citations"
        papers_params = {
            'user': user_id,
            'hl': 'en',
            'view_op': 'list_works',
            'sortby': 'pubdate',
            'cstart': '0',
            'pagesize': '100'
        }
        
        papers = []
        start_index = 0
        
        while True:
            papers_params['cstart'] = str(start_index)
            
            try:
                response = self.session.get(papers_url, params=papers_params)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all paper rows in the table
                paper_rows = soup.find_all('tr', class_='gsc_a_tr')
                
                if not paper_rows:
                    break
                    
                for row in paper_rows:
                    if max_papers and len(papers) >= max_papers:
                        return papers
                        
                    paper_info = self.extract_paper_info(row, user_id)
                    if paper_info:
                        # Check year limit if specified
                        if year_limit and paper_info.get('year'):
                            try:
                                paper_year = int(paper_info['year'])
                                if paper_year < year_limit:
                                    print(f"Reached year limit: found paper from {paper_year} (limit: {year_limit})")
                                    return papers
                            except (ValueError, TypeError):
                                # If year parsing fails, continue with the paper
                                pass
                        
                        papers.append(paper_info)
                
                # Check if there are more papers to fetch
                start_index += len(paper_rows)
                if len(paper_rows) < 100:  # Less than full page means we're done
                    break
                    
            except Exception as e:
                print(f"Error fetching papers: {e}")
                break
        
        return papers
    
    def extract_paper_info(self, row, user_id):
        """Extract basic paper information from a profile row"""
        paper_info = {}
        
        try:
            # Get title and link to detailed page
            title_cell = row.find('td', class_='gsc_a_t')
            if title_cell:
                title_link = title_cell.find('a')
                if title_link:
                    paper_info['title'] = title_link.get_text(strip=True)
                    # Build full URL for paper details
                    detail_href = title_link.get('href', '')
                    if detail_href:
                        paper_info['detail_url'] = urljoin(self.base_url, detail_href)
                
                # Get authors and publication info
                gray_divs = title_cell.find_all('div', class_='gs_gray')
                if len(gray_divs) >= 1:
                    paper_info['authors'] = gray_divs[0].get_text(strip=True)
                if len(gray_divs) >= 2:
                    paper_info['venue'] = gray_divs[1].get_text(strip=True)
            
            # Get citations count
            citations_cell = row.find('td', class_='gsc_a_c')
            if citations_cell:
                citations_link = citations_cell.find('a')
                if citations_link:
                    paper_info['citations'] = citations_link.get_text(strip=True)
                else:
                    paper_info['citations'] = '0'
            
            # Get year
            year_cell = row.find('td', class_='gsc_a_y')
            if year_cell:
                year_span = year_cell.find('span')
                if year_span:
                    paper_info['year'] = year_span.get_text(strip=True)
        
        except Exception as e:
            print(f"Error extracting paper info: {e}")
        
        return paper_info
    
    def get_paper_details(self, paper_detail_url):
        """Get detailed information for a specific paper"""
        try:
            with self.lock:
                print(f"Fetching details for: {paper_detail_url}")
            
            # Create a new session for this thread to avoid conflicts
            local_session = requests.Session()
            local_session.headers.update(self.session.headers)
            
            response = local_session.get(paper_detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Find the details table with id 'gsc_oci_table'
            details_table = soup.find('div', {'id': 'gsc_oci_table'})
            if details_table:
                # Look for div elements with class 'gs_scl' which contain field-value pairs
                rows = details_table.find_all('div', class_='gs_scl')
                
                for row in rows:
                    field_div = row.find('div', class_='gsc_oci_field')
                    value_div = row.find('div', class_='gsc_oci_value')
                    
                    if field_div and value_div:
                        field = field_div.get_text(strip=True)
                        value = value_div.get_text(strip=True)
                        details[field] = value
            
            # Look for abstract or description in a div with id 'gsc_oci_descr'
            description_div = soup.find('div', {'id': 'gsc_oci_descr'})
            if description_div:
                details['abstract'] = description_div.get_text(strip=True)
            
            # Add a small delay to be respectful to the server
            time.sleep(0.5)
            
            return details
            
        except Exception as e:
            with self.lock:
                print(f"Error getting paper details: {e}")
            return {}
    
    def analyze_author_research(self, author_name, max_papers=20, profile_index=0, num_workers=4, year_limit=None):
        """Complete workflow: find author, get papers, analyze research"""
        print(f"=== Analyzing research for: {author_name} ===")
        print(f"Using {num_workers} workers for parallel processing")
        if year_limit:
            print(f"Year limit: {year_limit} (will stop at papers from {year_limit-1} or earlier)")
        print()
        
        # Step 1: Find author profiles
        profiles = self.search_author_profiles(author_name)
        
        if not profiles:
            print("No profiles found!")
            return []
        
        print(f"Found {len(profiles)} profile(s):")
        for i, profile in enumerate(profiles):
            print(f"{i+1}. {profile['name']}")
            print(f"   Info: {profile['info']}")
            print(f"   URL: {profile['url']}")
        print()
        
        # Use the specified profile or the first one
        if profile_index >= len(profiles):
            print(f"Profile index {profile_index} out of range, using profile 0")
            profile_index = 0
            
        chosen_profile = profiles[profile_index]
        print(f"Using profile: {chosen_profile['name']}")
        
        # Step 2: Get papers from profile
        papers = self.get_profile_papers(chosen_profile['url'], max_papers, year_limit)
        
        print(f"\nFound {len(papers)} papers")
        print(f"Fetching detailed information using {num_workers} parallel workers...")
        
        # Step 3: Get detailed info for each paper using parallel processing
        papers_to_process = papers[:max_papers]
        
        def process_paper(paper_data):
            paper, index = paper_data
            try:
                # Get detailed information
                if 'detail_url' in paper:
                    details = self.get_paper_details(paper['detail_url'])
                    paper.update(details)
                
                return paper, index
            except Exception as e:
                with self.lock:
                    print(f"Error processing paper {index + 1}: {e}")
                return paper, index
        
        # Create list of (paper, index) tuples for processing
        paper_data = [(paper, i) for i, paper in enumerate(papers_to_process)]
        
        # Process papers in parallel
        detailed_papers = [None] * len(papers_to_process)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = executor.map(process_paper, paper_data)
            
            for paper, index in results:
                detailed_papers[index] = paper
        
        # Display results
        print(f"\n=== Research Summary ===")
        for i, paper in enumerate(detailed_papers, 1):
            print(f"\n--- Paper {i}: {paper['title'][:80]}{'...' if len(paper['title']) > 80 else ''} ---")
            print(f"Year: {paper.get('year', 'Unknown')}")
            print(f"Citations: {paper.get('citations', '0')}")
            print(f"Authors: {paper.get('authors', 'Unknown')}")
            print(f"Venue: {paper.get('venue', 'Unknown')}")
            
            if 'abstract' in paper:
                print(f"Abstract: {paper['abstract'][:500]}{'...' if len(paper['abstract']) > 500 else ''}")
            elif 'Description' in paper:
                print(f"Description: {paper['Description'][:500]}{'...' if len(paper['Description']) > 500 else ''}")
            
            # Show some other details we extracted
            if 'Journal' in paper:
                print(f"Journal: {paper['Journal']}")
            if 'Volume' in paper:
                print(f"Volume: {paper['Volume']}")
            if 'Pages' in paper:
                print(f"Pages: {paper['Pages']}")
            if 'Publisher' in paper:
                print(f"Publisher: {paper['Publisher']}")
            if 'Total citations' in paper:
                print(f"Scholar Citations: {paper['Total citations']}")
        
        return detailed_papers

def main():
    parser = argparse.ArgumentParser(description='Parse Google Scholar author profiles')
    parser.add_argument('author', help='Author name to search for')
    parser.add_argument('--max-papers', type=int, default=20, help='Maximum number of papers to analyze')
    parser.add_argument('--profile-index', type=int, default=0, help='Which profile to use (0 for first, 1 for second, etc.)')
    parser.add_argument('--num-workers', type=int, default=4, help='Number of parallel workers for fetching paper details')
    parser.add_argument('--year-limit', type=int, help='Stop collecting papers when reaching this year (e.g., --year-limit 2020 stops at 2019 papers)')
    parser.add_argument('--output', help='Output file to save results (JSON format)')
    
    args = parser.parse_args()
    
    scholar_parser = ScholarProfileParser()
    papers = scholar_parser.analyze_author_research(args.author, args.max_papers, args.profile_index, args.num_workers, args.year_limit)
    
    if args.output and papers:
        with open(args.output, 'w') as f:
            json.dump(papers, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
