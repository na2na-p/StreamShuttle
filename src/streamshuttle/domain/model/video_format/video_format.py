"""
VideoFormat Aggregateモジュール

VideoFormat Aggregateを定義します。
"""

from dataclasses import dataclass

from streamshuttle.domain.model.video_format.codec import Codec
from streamshuttle.domain.model.video_format.format_id import FormatId
from streamshuttle.domain.model.video_format.quality import Quality


@dataclass(frozen=True)
class VideoFormat:
    """
    VideoFormat Aggregate

    YouTube動画のストリーム形式情報を管理します。
    このAggregateは不変であり、フォーマットID、画質、コーデックの情報を
    一つの整合性のある単位として表現します。

    Aggregateルートとして、FormatId、Quality、Codecの各ValueObjectを
    集約し、一貫性のある境界を形成します。

    ID設計:
        このAggregateのIDは _format_id (FormatId型) です。
        frozen=True により、ID（_format_id）の不変性が保証されています。
        同一のフォーマットIDに対するビデオフォーマットは一意に識別されます。

    Attributes:
        _format_id: フォーマットID（このAggregateの識別子）
        _quality: 画質情報
        _codec: コーデック情報
    """

    _format_id: FormatId
    _quality: Quality
    _codec: Codec

    @property
    def format_id(self) -> FormatId:
        """
        フォーマットIDを取得します

        Returns:
            FormatId: フォーマットID
        """
        return self._format_id

    @property
    def quality(self) -> Quality:
        """
        画質情報を取得します

        Returns:
            Quality: 画質情報
        """
        return self._quality

    @property
    def codec(self) -> Codec:
        """
        コーデック情報を取得します

        Returns:
            Codec: コーデック情報
        """
        return self._codec
