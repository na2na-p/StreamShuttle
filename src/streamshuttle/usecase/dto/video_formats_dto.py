from pydantic import BaseModel, ConfigDict

from streamshuttle.usecase.dto.video_format_dto import VideoFormatDto
from streamshuttle.usecase.dto.video_info_dto import VideoInfoDto


class VideoFormatsDto(BaseModel):
    """
    ビデオフォーマット統合 DTO

    動画情報とフォーマット一覧を統合して保持します。
    キャッシュのシリアライズ/デシリアライズに使用されます。

    Attributes:
        video_info: 動画基本情報
        formats: 利用可能なフォーマット一覧
    """

    model_config = ConfigDict(frozen=True)

    video_info: VideoInfoDto
    formats: list[VideoFormatDto]
