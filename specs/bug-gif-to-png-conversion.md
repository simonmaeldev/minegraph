# Bug: GIF Images Downloaded as PNG Causing Matplotlib Errors

## Bug Description
The image downloader script (`src/download_item_images.py`) downloads images from Minecraft Wiki and saves them with a `.png` extension. However, some of the downloaded images are actually GIF files (animated or static), not PNG files. When the 3D visualization script (`src/visualize_graph_3d.py`) tries to load these GIF files using matplotlib's `imread()` function, it fails because matplotlib expects PNG format based on the file extension. This causes the visualization to fail or skip these items, resulting in missing nodes in the 3D graph.

**Symptoms:**
- Some downloaded images have `.png` extension but are actually GIF format
- Matplotlib fails to load these files or displays them incorrectly
- 3D visualization falls back to spheres for these items instead of displaying images
- Currently 64 out of ~850 items are affected

**Expected Behavior:**
All downloaded images should be in PNG format so matplotlib can load them correctly for the 3D visualization.

**Actual Behavior:**
Some images are GIF files saved with `.png` extension, causing compatibility issues with matplotlib.

## Problem Statement
The Minecraft Wiki serves some item images as GIF files (particularly for animated items like banners, chests, campfires, clocks, and compasses). The download script saves these files with a `.png` extension without checking or converting the actual file format. This format mismatch breaks the image-based 3D visualization feature.

## Solution Statement
Add a post-download conversion pass to the image downloader script that:
1. Detects the actual file format of each downloaded image using the `file` command or Python's `imghdr` module
2. If an image is a GIF, converts it to PNG format using a CLI tool (ImageMagick or ffmpeg)
3. Replaces the original GIF file with the converted PNG file
4. Logs the conversion for transparency

This approach ensures all images in the `images/` directory are truly PNG format, maintaining compatibility with matplotlib and the visualization system.

## Steps to Reproduce
1. Run the image downloader: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/`
2. Check downloaded file formats: `file images/*.png | grep -i gif`
3. Observe that 64 files with `.png` extension are actually GIF format
4. Try to visualize with images: `uv run python src/visualize_graph_3d.py --use-images`
5. Observe that items with GIF files fail to load or display incorrectly

## Root Cause Analysis
The root cause is in the `download_image()` function in `src/download_item_images.py` (lines 129-178). This function:
1. Downloads the raw image bytes from the wiki URL
2. Saves them directly to disk with a `.png` extension
3. Does NOT validate or convert the actual file format

The Minecraft Wiki serves different file formats for different items:
- Most items: PNG format (works correctly)
- Animated items (banners, chests, campfires, clocks, compasses, etc.): GIF format (causes issues)

The script assumes all images are PNG based on the standardized filename, but doesn't verify or convert the actual format. This breaks the contract expected by matplotlib in the visualization script.

## Relevant Files
Use these files to fix the bug:

- **src/download_item_images.py** (lines 129-178) - Contains the `download_image()` function that needs modification to detect and convert GIF files to PNG after downloading. This is the main file requiring changes.

- **src/download_item_images.py** (lines 181-323) - Contains the `main()` function that orchestrates the download process. May need a new conversion pass after downloads complete, or integration of conversion into the download loop.

- **tests/test_download_item_images.py** - Test suite that needs additional tests for GIF detection and conversion functionality to ensure the bug fix works correctly.

- **README.md** (lines 93-133) - Documentation for the image downloader that should be updated to mention automatic GIF-to-PNG conversion.

- **pyproject.toml** - May need to add new dependencies if using Python libraries for image format detection (e.g., Pillow), though CLI tools like ImageMagick or ffmpeg are preferred to avoid heavy dependencies.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Research and Choose Conversion Tool
- Check which image conversion CLI tools are available on the system (ImageMagick's `convert`, GraphicsMagick's `gm`, or ffmpeg)
- Since ffmpeg is available at `/usr/bin/ffmpeg`, plan to use it for GIF-to-PNG conversion
- Research the correct ffmpeg command: `ffmpeg -i input.gif output.png` (with appropriate flags for quality and first frame extraction)
- Verify that the Pillow library is available (comes with matplotlib) for format detection as a Python alternative

### 2. Implement Format Detection Function
- Add a new function `detect_image_format(file_path: str) -> str` to `src/download_item_images.py`
- Use Python's `imghdr.what()` or Pillow's `Image.open().format` to detect actual file format
- Return the format as a string (e.g., "gif", "png", "jpeg")
- Handle errors gracefully and return "unknown" if detection fails
- Add logging for debugging format detection issues

### 3. Implement GIF-to-PNG Conversion Function
- Add a new function `convert_gif_to_png(gif_path: str, png_path: str) -> bool` to `src/download_item_images.py`
- Use `subprocess.run()` to call ffmpeg: `ffmpeg -i {gif_path} -vframes 1 -y {png_path}`
- The `-vframes 1` flag extracts only the first frame (important for animated GIFs)
- The `-y` flag overwrites the output file without prompting
- Return True if conversion succeeds, False otherwise
- Log conversion attempts and results
- Handle subprocess errors with try-except and proper error messages

### 4. Integrate Conversion into Download Process
- Modify the `download_image()` function to accept an optional `convert_gifs: bool` parameter
- After saving the downloaded image, call `detect_image_format()` to check the actual format
- If format is "gif" and `convert_gifs` is True, call `convert_gif_to_png()` to convert in-place
- Log each conversion for transparency
- Update file size validation to run after conversion (if conversion happened)

### 5. Add Conversion Pass to Main Function
- Update the `main()` function to add a `--convert-gifs` flag (default: True)
- Pass this flag to the `download_image()` function
- Add conversion statistics to the summary report (e.g., "Converted GIFs: 64")
- Ensure the conversion happens for both new downloads and cached images (when using `--force-redownload`)

### 6. Add Tests for Format Detection
- Add new test class `TestFormatDetection` to `tests/test_download_item_images.py`
- Test `detect_image_format()` with various file types: PNG, GIF, JPEG, corrupted files
- Use temporary files with known formats for testing
- Verify correct format strings are returned
- Test error handling for non-existent files

### 7. Add Tests for GIF Conversion
- Add new test class `TestGIFConversion` to `tests/test_download_item_images.py`
- Mock `subprocess.run()` to test `convert_gif_to_png()` without actually running ffmpeg
- Test successful conversion scenarios
- Test conversion failure scenarios (ffmpeg not found, invalid input file, etc.)
- Test that correct ffmpeg command is constructed
- Verify error handling and logging

### 8. Add Integration Tests
- Add integration test that downloads a known GIF image and verifies conversion
- Use a mock GIF file for testing to avoid network dependency
- Verify that the output file is actually PNG format after conversion
- Test the full download-and-convert pipeline end-to-end

### 9. Test with Real Data
- Run the downloader on a small subset of items known to have GIFs: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 100 --force-redownload --verbose`
- Verify that GIF files are detected and converted
- Check the conversion statistics in the summary report
- Manually verify a few converted files: `file images/black_banner.png images/compass.png`

### 10. Run Full Test Suite
- Execute all tests to ensure no regressions: `uv run pytest tests/ -v`
- Fix any failing tests
- Ensure all new tests pass
- Verify code coverage for new functions

### 11. Update Documentation
- Update README.md section "Download Item Images" (lines 93-133) to mention automatic GIF-to-PNG conversion
- Document the `--convert-gifs` flag in the command-line options list
- Add a note explaining why conversion is necessary (matplotlib compatibility)
- Mention that ffmpeg is required for the conversion feature

### 12. Run Full Conversion on All Images
- Run the downloader on all items with conversion enabled: `uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --force-redownload --verbose --convert-gifs`
- Monitor the conversion process and verify all 64 GIFs are converted
- Check the summary report for conversion statistics

### 13. Validate 3D Visualization with Converted Images
- Run the 3D visualization with images: `uv run python src/visualize_graph_3d.py --use-images --verbose`
- Verify that items previously failing (banners, chests, compass, clock, etc.) now display correctly
- Check that no errors are logged for image loading
- Confirm all images load successfully and display in the 3D graph

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run all existing tests to ensure no regressions
uv run pytest tests/ -v

# Test image downloader with conversion on a small subset
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --limit 10 --force-redownload --verbose --convert-gifs

# Verify that GIF files with .png extension are now true PNG files
file images/black_banner.png images/compass.png images/clock.png images/campfire.png

# Run specific tests for the new functionality
uv run pytest tests/test_download_item_images.py::TestFormatDetection -v
uv run pytest tests/test_download_item_images.py::TestGIFConversion -v

# Test the full download process with conversion on all items
uv run python src/download_item_images.py --input output/items.csv --output-dir images/ --force-redownload --verbose

# Verify no GIF files remain with .png extension
file images/*.png | grep -i gif | wc -l  # Should output 0

# Test 3D visualization with images to ensure matplotlib can load all images
uv run python src/visualize_graph_3d.py --use-images --verbose

# Run all tests again to confirm everything works
uv run pytest tests/ -v
```

## Notes

### Why This Approach?
This surgical fix solves the exact problem without overengineering:
1. **Minimal changes**: Only adds format detection and conversion, doesn't restructure existing code
2. **Backward compatible**: Conversion is optional via flag, doesn't break existing workflows
3. **Uses available tools**: Leverages ffmpeg which is already installed on the system
4. **Preserves caching**: Conversion works with existing cache logic
5. **Clear logging**: Users can see exactly which files are converted

### Alternative Approaches Considered
1. **Download as GIF, convert to PNG separately**: More complex, requires two-pass system
2. **Use Pillow for conversion**: Adds heavy dependency, ffmpeg is already available
3. **Change file extension to .gif**: Breaks matplotlib compatibility, doesn't solve the problem
4. **Download different image format**: Minecraft Wiki doesn't offer alternative formats for animated items

### Why ffmpeg?
- Already installed on the system (`/usr/bin/ffmpeg`)
- Lightweight for this use case (just extracting first frame)
- Widely available on most systems
- Handles animated GIFs correctly with `-vframes 1` flag
- No additional dependencies needed

### ImageMagick Alternative
If ffmpeg is not available, the code can fall back to ImageMagick's `convert` command:
```bash
convert input.gif[0] output.png  # [0] extracts first frame
```

However, since ffmpeg is already present, we'll use it as the primary conversion tool.

### Performance Considerations
- Conversion adds ~0.1-0.5 seconds per GIF file
- With 64 GIFs out of 850 items, this adds ~6-32 seconds to the full download
- This is acceptable given the download already takes 5-10 minutes total
- Conversion is cached (converted files won't be re-converted unless forced)

### Edge Cases to Handle
- Animated GIFs: Extract first frame only using `-vframes 1`
- Large GIFs: ffmpeg handles efficiently, no special handling needed
- Corrupted GIFs: ffmpeg will fail, log error and keep original file
- Permission errors: Handle with proper error messages
- Disk space: Converted PNGs may be larger, but difference is negligible

### Dependencies Required
- **ffmpeg**: Already installed at `/usr/bin/ffmpeg`
- **Python imghdr or Pillow**: Already available (Pillow comes with matplotlib)
- No new dependencies need to be added to `pyproject.toml`
