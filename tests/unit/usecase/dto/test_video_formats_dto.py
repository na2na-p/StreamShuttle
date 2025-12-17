import pytest

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_formats_dto import VideoFormatsDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


@pytest.mark.parametrize(
    "video_info, formats",
    [
        pytest.param(
            VideoInfoDto(
                video_id="dQw4w9WgXcQ",
                title="Test Video",
                thumbnail_url="https://example.com/thumb.jpg",
            ),
            [
                VideoFormatDto(
                    format_id="137",
                    quality="1080p",
                    codec="avc1",
                    url="https://example.com/video.mp4",
                    has_audio=False,
                    has_video=True,
                )
            ],
            id="正常系: 動画情報とフォーマット一覧を保持するDTOが作成される",
        ),
        pytest.param(
            VideoInfoDto(
                video_id="test123",
                title="Another Video",
                thumbnail_url="https://example.com/another.jpg",
            ),
            [],
            id="正常系: フォーマット一覧が空のDTOが作成される",
        ),
    ],
)
def test_video_formats_dto_initialization(video_info: VideoInfoDto, formats: list[VideoFormatDto]):
    """正常系: VideoFormatsDtoが正しく初期化される"""
    # Act
    dto = VideoFormatsDto(video_info=video_info, formats=formats)

    # Assert
    assert dto.video_info == video_info
    assert dto.formats == formats


def test_video_formats_dto_is_immutable():
    """正常系: DTOは不変である"""
    # Arrange
    dto = VideoFormatsDto(
        video_info=VideoInfoDto(
            video_id="test",
            title="Test",
            thumbnail_url="https://example.com/thumb.jpg",
        ),
        formats=[],
    )

    # Act & Assert
    with pytest.raises(Exception):
        dto.video_info = VideoInfoDto(
            video_id="changed",
            title="Changed",
            thumbnail_url="https://example.com/changed.jpg",
        )


def test_video_formats_dto_with_multiple_formats():
    """正常系: 複数のフォーマットを保持するDTOが作成される"""
    # Arrange
    video_info = VideoInfoDto(
        video_id="multi",
        title="Multi Format Video",
        thumbnail_url="https://example.com/multi.jpg",
    )
    formats = [
        VideoFormatDto(
            format_id="137",
            quality="1080p",
            codec="avc1",
            url="https://example.com/video1.mp4",
            has_audio=False,
            has_video=True,
        ),
        VideoFormatDto(
            format_id="140",
            quality="audio",
            codec="mp4a",
            url="https://example.com/audio.m4a",
            has_audio=True,
            has_video=False,
        ),
    ]

    # Act
    dto = VideoFormatsDto(video_info=video_info, formats=formats)

    # Assert
    assert dto.video_info == video_info
    assert len(dto.formats) == 2
    assert dto.formats[0].format_id == "137"
    assert dto.formats[1].format_id == "140"
