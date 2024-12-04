#!/bin/bash

# Find all files named system.md
find . -type f -name "system.md" | while read -r file; do
  # Get the parent directory name
  parent_dir=$(basename "$(dirname "$file")")
  # Construct the new file name
  new_file="$(dirname "$file")/$parent_dir.md"
  # Rename the file
  #echo "Renaming $file to $new_file"
  mv "$file" "$new_file"
done