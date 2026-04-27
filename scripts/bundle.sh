#!/bin/bash

tmp_dir=$(mktemp -d)

root_dir="$(dirname "$0")/.."
root_dir=$(realpath "$root_dir")
dist_dir="$root_dir/dist"

cd "$root_dir"

uv build

mkdir -p "$tmp_dir"/test
mkdir -p "$tmp_dir"/generated

cp dist/*.whl "$tmp_dir"/
cp prompts/instructions-prompt.md "$tmp_dir"/
cp test/*.py "$tmp_dir"/test/

for g in generated_cottage.py generated_apartment.py generated_lighthouse.py; do
    cp "generated/$g" "$tmp_dir"/generated/
done

cd "$tmp_dir"

zip -r py4bricks-bundle.zip ./*

mv py4bricks-bundle.zip "$dist_dir"/

echo "Bundle for uploading to ChatGPT/Claude Chat created at: $OLDPWD/dist/py4bricks-bundle.zip"
