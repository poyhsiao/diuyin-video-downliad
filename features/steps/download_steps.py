"""Step definitions for download feature."""

import pytest




@pytest.fixture
def mock_extract(mocker):
    """Mock the extract_cdn_url function."""
    return mocker.patch("douyin_download.extractor.extract_cdn_url")
