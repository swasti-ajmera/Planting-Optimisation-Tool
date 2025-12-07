"""
Pytest configuration file for tests folder
"""
import pytest
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default test environment variables
os.environ.setdefault("SECRET_KEY", "DTaCnhWSbCoUJA34I-43zIlx708z3ELnw2iroqhqnbg")
os.environ.setdefault("PUBLIC_SUPABASE_URL", "https://jtkoqhrjayikmhfhljai.supabase.co")
os.environ.setdefault("PUBLIC_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp0a29xaHJqYXlpa21oZmhsamFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ4NDYzNTMsImV4cCI6MjA4MDQyMjM1M30.DHC1tHQu9RB-L07f0tsibA2PwWP0H8fOnofxNRAr9AM")