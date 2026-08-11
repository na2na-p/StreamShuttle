"""
ストリームURLレスポンスモデル定義モジュール

GET /playlist/stream エンドポイントのレスポンス構造を定義します。
"""

from pydantic import BaseModel, ConfigDict, Field


class StreamUrlResponse(BaseModel):
    """
    ストリームURLレスポンスモデル

    プレイヤーが<video>要素に直接設定するための解決済みストリームURLを表現します。
    リダイレクト（307）ではなくJSONで返すことで、シークのたびに解決処理へ
    リクエストが飛ぶことを避けています。

    Attributes:
        video_id: YouTube動画ID
        stream_url: 解決済みの直接ストリームURL
    """

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(..., description="YouTube動画ID")
    stream_url: str = Field(..., description="解決済みの直接ストリームURL")
