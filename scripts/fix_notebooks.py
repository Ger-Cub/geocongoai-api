import json
import os
import re

notebooks_dir = "/home/gerard/Documents/GeoKivuDoc/geocongoai-api/notebooks"

def fix_notebook_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple fix: identify double quotes inside markdown source strings and replace with single quotes
    # This is tricky because the JSON is already broken.
    # We can try to fix it by searching for patterns like : [ ..., "text "inner" text", ... ]
    
    # Alternative: rewrite the files using a safe method.
    # Since I know the content I wrote, I can just repeat the write_to_file calls but properly escaped.
    pass

# Instead of a complex script, I will just manually fix the 15 files using write_to_file with properly escaped strings.
# I will use single quotes for all "highlights" in the markdown cells.
