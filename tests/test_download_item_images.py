"""
Tests for the image downloader module.
"""

import os
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from PIL import Image

from src.download_item_images import (
    convert_gif_to_png,
    detect_image_format,
    download_image,
    extract_image_url_from_page,
    load_items_from_csv,
    standardize_filename,
)


class TestFilenameStandardization:
    """Test filename standardization."""

    def test_simple_name(self):
        """Test simple item name."""
        assert standardize_filename("Iron Ingot") == "iron_ingot.png"

    def test_multiple_spaces(self):
        """Test item name with multiple spaces."""
        assert standardize_filename("Iron  Ingot") == "iron_ingot.png"

    def test_lowercase(self):
        """Test already lowercase name."""
        assert standardize_filename("iron ingot") == "iron_ingot.png"

    def test_special_characters(self):
        """Test name with special characters."""
        assert standardize_filename("Iron-Ingot!") == "ironingot.png"

    def test_mixed_case(self):
        """Test mixed case name."""
        assert standardize_filename("IrOn InGoT") == "iron_ingot.png"

    def test_numbers(self):
        """Test name with numbers."""
        assert standardize_filename("TNT 64") == "tnt_64.png"

    def test_parentheses(self):
        """Test name with parentheses."""
        assert standardize_filename("Boat (Oak)") == "boat_oak.png"


class TestCSVLoading:
    """Test CSV loading functionality."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("item_name,item_url\n")
            f.write("Iron Ingot,https://minecraft.wiki/w/Iron_Ingot\n")
            f.write("Gold Ingot,https://minecraft.wiki/w/Gold_Ingot\n")
            csv_path = f.name

        try:
            items = load_items_from_csv(csv_path)
            assert len(items) == 2
            assert items[0]["item_name"] == "Iron Ingot"
            assert items[0]["item_url"] == "https://minecraft.wiki/w/Iron_Ingot"
            assert items[1]["item_name"] == "Gold Ingot"
        finally:
            os.unlink(csv_path)

    def test_load_empty_csv(self):
        """Test loading an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("item_name,item_url\n")
            csv_path = f.name

        try:
            items = load_items_from_csv(csv_path)
            assert len(items) == 0
        finally:
            os.unlink(csv_path)

    def test_load_nonexistent_csv(self):
        """Test loading a nonexistent CSV file."""
        with pytest.raises(Exception):
            load_items_from_csv("/nonexistent/file.csv")


class TestImageURLExtraction:
    """Test image URL extraction from wiki pages."""

    @patch("src.download_item_images.requests.get")
    def test_extract_valid_infobox_image(self, mock_get):
        """Test extracting image from valid infobox."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="infobox">
                <img src="//example.com/iron_ingot.png" />
            </div>
        </html>
        """
        mock_get.return_value = mock_response

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url == "https://example.com/iron_ingot.png"

    @patch("src.download_item_images.requests.get")
    def test_extract_skip_inventory_images(self, mock_get):
        """Test that inventory images are skipped."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="infobox-invimages">
                <img src="//example.com/inventory.png" />
            </div>
            <div class="infobox">
                <img src="//example.com/iron_ingot.png" />
            </div>
        </html>
        """
        mock_get.return_value = mock_response

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url == "https://example.com/iron_ingot.png"

    @patch("src.download_item_images.requests.get")
    def test_extract_no_infobox(self, mock_get):
        """Test page with no infobox."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="content">
                <img src="//example.com/some_image.png" />
            </div>
        </html>
        """
        mock_get.return_value = mock_response

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url is None

    @patch("src.download_item_images.requests.get")
    def test_extract_no_image_in_infobox(self, mock_get):
        """Test infobox with no image."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="infobox">
                <p>Some text</p>
            </div>
        </html>
        """
        mock_get.return_value = mock_response

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url is None

    @patch("src.download_item_images.requests.get")
    def test_extract_request_error(self, mock_get):
        """Test handling of request errors."""
        mock_get.side_effect = requests.RequestException("Network error")

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url is None

    @patch("src.download_item_images.requests.get")
    def test_extract_relative_url(self, mock_get):
        """Test handling of relative URLs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <div class="infobox">
                <img src="/images/iron_ingot.png" />
            </div>
        </html>
        """
        mock_get.return_value = mock_response

        image_url = extract_image_url_from_page("https://minecraft.wiki/w/Iron_Ingot")
        assert image_url.startswith("https://minecraft.wiki/")


class TestImageDownload:
    """Test image downloading functionality."""

    @patch("src.download_item_images.requests.get")
    def test_download_success(self, mock_get):
        """Test successful image download."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake image data" * 100  # Make it larger than min_size
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            success, converted = download_image("https://example.com/image.png", output_path, convert_gifs=False)

            assert success is True
            assert converted is False
            assert os.path.exists(output_path)

            with open(output_path, "rb") as f:
                assert f.read() == mock_response.content

    @patch("src.download_item_images.requests.get")
    def test_download_request_error(self, mock_get):
        """Test download with request error."""
        mock_get.side_effect = requests.RequestException("Network error")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            success, converted = download_image("https://example.com/image.png", output_path)

            assert success is False
            assert converted is False
            assert not os.path.exists(output_path)

    @patch("src.download_item_images.requests.get")
    def test_download_small_file_warning(self, mock_get, caplog):
        """Test warning for suspiciously small files."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"tiny"  # Smaller than min_size
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            success, converted = download_image("https://example.com/image.png", output_path, convert_gifs=False)

            assert success is True
            assert converted is False
            # Check that file was still saved despite warning
            assert os.path.exists(output_path)

    @patch("src.download_item_images.requests.get")
    def test_download_http_error(self, mock_get):
        """Test download with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            success, converted = download_image("https://example.com/image.png", output_path)

            assert success is False
            assert converted is False


class TestFormatDetection:
    """Test image format detection."""

    def test_detect_png_format(self):
        """Test detecting PNG format."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a valid PNG image
            img = Image.new("RGB", (10, 10), color="red")
            img.save(f, format="PNG")
            png_path = f.name

        try:
            format_type = detect_image_format(png_path)
            assert format_type == "png"
        finally:
            os.unlink(png_path)

    def test_detect_gif_format(self):
        """Test detecting GIF format."""
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
            # Create a valid GIF image
            img = Image.new("RGB", (10, 10), color="blue")
            img.save(f, format="GIF")
            gif_path = f.name

        try:
            format_type = detect_image_format(gif_path)
            assert format_type == "gif"
        finally:
            os.unlink(gif_path)

    def test_detect_jpeg_format(self):
        """Test detecting JPEG format."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            # Create a valid JPEG image
            img = Image.new("RGB", (10, 10), color="green")
            img.save(f, format="JPEG")
            jpeg_path = f.name

        try:
            format_type = detect_image_format(jpeg_path)
            assert format_type == "jpeg"
        finally:
            os.unlink(jpeg_path)

    def test_detect_unknown_format(self):
        """Test detecting unknown format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b'not an image file')
            unknown_path = f.name

        try:
            format_type = detect_image_format(unknown_path)
            assert format_type == "unknown"
        finally:
            os.unlink(unknown_path)

    def test_detect_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        format_type = detect_image_format("/nonexistent/file.png")
        assert format_type == "unknown"


class TestGIFConversion:
    """Test GIF to PNG conversion."""

    @patch("src.download_item_images.subprocess.run")
    def test_convert_gif_success(self, mock_run):
        """Test successful GIF conversion."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        success = convert_gif_to_png("/tmp/test.gif", "/tmp/test.png")

        assert success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert "/tmp/test.gif" in args
        assert "-vframes" in args
        assert "1" in args
        assert "/tmp/test.png" in args

    @patch("src.download_item_images.subprocess.run")
    def test_convert_gif_failure(self, mock_run):
        """Test failed GIF conversion."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ffmpeg error"
        mock_run.return_value = mock_result

        success = convert_gif_to_png("/tmp/test.gif", "/tmp/test.png")

        assert success is False

    @patch("src.download_item_images.subprocess.run")
    def test_convert_gif_timeout(self, mock_run):
        """Test GIF conversion timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 30)

        success = convert_gif_to_png("/tmp/test.gif", "/tmp/test.png")

        assert success is False

    @patch("src.download_item_images.subprocess.run")
    def test_convert_gif_ffmpeg_not_found(self, mock_run):
        """Test GIF conversion when ffmpeg not found."""
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")

        success = convert_gif_to_png("/tmp/test.gif", "/tmp/test.png")

        assert success is False


class TestIntegration:
    """Integration tests."""

    def test_standardize_and_save(self):
        """Test standardizing filename and saving to disk."""
        item_name = "Iron Ingot"
        filename = standardize_filename(item_name)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, filename)

            # Simulate saving a file
            with open(output_path, "wb") as f:
                f.write(b"fake image data")

            # Verify
            assert os.path.exists(output_path)
            assert os.path.basename(output_path) == "iron_ingot.png"

    @patch("src.download_item_images.subprocess.run")
    @patch("src.download_item_images.requests.get")
    def test_download_and_convert_gif(self, mock_get, mock_subprocess):
        """Test end-to-end download and GIF conversion."""
        # Create a proper GIF image in memory
        gif_buffer = BytesIO()
        img = Image.new("RGB", (10, 10), color="red")
        img.save(gif_buffer, format="GIF")
        gif_content = gif_buffer.getvalue()

        # Mock downloading a GIF file
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = gif_content
        mock_get.return_value = mock_response

        # Mock successful ffmpeg conversion that creates the output file
        def mock_ffmpeg_run(cmd, **kwargs):
            # Extract output path from command
            if "-i" in cmd and len(cmd) > cmd.index("-i") + 1:
                output_path = cmd[-1]  # Last argument is output path
                # Create a PNG file at the output path
                png_img = Image.new("RGB", (10, 10), color="red")
                png_img.save(output_path, format="PNG")

            mock_result = Mock()
            mock_result.returncode = 0
            return mock_result

        mock_subprocess.side_effect = mock_ffmpeg_run

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")

            # Download with conversion enabled
            success, converted = download_image(
                "https://example.com/image.gif",
                output_path,
                convert_gifs=True
            )

            # Verify download succeeded
            assert success is True
            # Verify conversion was attempted
            assert converted is True
            # Verify ffmpeg was called
            mock_subprocess.assert_called_once()


class TestMainFunction:
    """Test the main function and end-to-end behavior."""

    @patch("src.download_item_images.extract_image_url_from_page")
    @patch("src.download_item_images.download_image")
    @patch("src.download_item_images.load_items_from_csv")
    def test_failed_items_tracking(
        self, mock_load_items, mock_download_image, mock_extract_url
    ):
        """Test that failed items are tracked in a list and displayed in summary."""
        # Setup mock data
        mock_load_items.return_value = [
            {"item_name": "Iron Ingot", "item_url": "https://minecraft.wiki/w/Iron_Ingot"},
            {"item_name": "Chain", "item_url": "https://minecraft.wiki/w/Chain"},
            {"item_name": "Gold Ingot", "item_url": "https://minecraft.wiki/w/Gold_Ingot"},
            {"item_name": "Head", "item_url": "https://minecraft.wiki/w/Head"},
        ]

        # Chain and Head fail to extract URL
        def extract_url_side_effect(url):
            if "Chain" in url or "Head" in url:
                return None
            return "https://example.com/image.png"

        mock_extract_url.side_effect = extract_url_side_effect
        mock_download_image.return_value = (True, False)  # success, not converted

        with tempfile.TemporaryDirectory() as tmpdir:
            # Import main here to avoid module-level execution
            from src.download_item_images import main
            import sys

            # Mock command line arguments
            test_args = [
                "download_item_images.py",
                "--input", "dummy.csv",
                "--output-dir", tmpdir,
            ]
            with patch.object(sys, "argv", test_args):
                # Capture stdout to check summary
                from io import StringIO
                with patch("sys.stdout", new=StringIO()) as fake_stdout:
                    result = main()

                    output = fake_stdout.getvalue()

                    # Verify failed items are listed
                    assert "Failed items:" in output
                    assert "- Chain" in output
                    assert "- Head" in output
                    assert "Failed:                2" in output

                    # Verify exit code (should be 1 if there are failures)
                    assert result == 1

    @patch("src.download_item_images.extract_image_url_from_page")
    @patch("src.download_item_images.download_image")
    @patch("src.download_item_images.load_items_from_csv")
    def test_cached_items_skipped_early(
        self, mock_load_items, mock_download_image, mock_extract_url, caplog
    ):
        """Test that cached items are skipped early without unnecessary processing."""
        import logging
        caplog.set_level(logging.DEBUG)

        # Setup mock data
        mock_load_items.return_value = [
            {"item_name": "Iron Ingot", "item_url": "https://minecraft.wiki/w/Iron_Ingot"},
            {"item_name": "Gold Ingot", "item_url": "https://minecraft.wiki/w/Gold_Ingot"},
        ]

        mock_extract_url.return_value = "https://example.com/image.png"
        mock_download_image.return_value = (True, False)  # success, not converted

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cached file for Iron Ingot
            cached_file = Path(tmpdir) / "iron_ingot.png"
            cached_file.write_bytes(b"cached image")

            # Import main here
            from src.download_item_images import main
            import sys

            # Mock command line arguments with verbose mode
            test_args = [
                "download_item_images.py",
                "--input", "dummy.csv",
                "--output-dir", tmpdir,
                "--verbose",
            ]
            with patch.object(sys, "argv", test_args):
                from io import StringIO
                with patch("sys.stdout", new=StringIO()):
                    main()

                    # Check that extract_image_url_from_page was NOT called for Iron Ingot
                    # It should only be called once (for Gold Ingot)
                    assert mock_extract_url.call_count == 1

                    # Check log messages show skipping
                    log_messages = [record.message for record in caplog.records]
                    skip_messages = [msg for msg in log_messages if "Skipping (already cached)" in msg]
                    assert len(skip_messages) == 1
                    assert "Iron Ingot" in skip_messages[0]
