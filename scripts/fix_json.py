import os
import re

notebooks_dir = "/home/gerard/Documents/GeoKivuDoc/geocongoai-api/notebooks"

for filename in os.listdir(notebooks_dir):
    if filename.endswith(".ipynb"):
        path = os.path.join(notebooks_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            # We are looking for lines like: "   \"content with \"internal\" quotes\",\n"
            # It's usually inside "source": [ ... ]
            # The JSON structure uses " for keys and values.
            # A line in source looks like: "    \"markdown text with \\\"quote\\\" \",\n"
            # If it's broken, it looks like: "    \"markdown text with \"quote\" \",\n"
            
            # Simple heuristic: if a line starts with whitespace and " and ends with ",\n or "\n
            # and has " in the middle, we replace middle " with '
            match = re.match(r'^(\s+)"(.*)"(,?)\n$', line)
            if match:
                indent = match.group(1)
                content = match.group(2)
                comma = match.group(3)
                # Replace inner double quotes with single quotes
                # But don't touch escaped ones if any (though here they are unescaped)
                fixed_content = content.replace('"', "'")
                new_lines.append(f'{indent}"{fixed_content}"{comma}\n')
            else:
                new_lines.append(line)
        
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Fixed {filename}")
