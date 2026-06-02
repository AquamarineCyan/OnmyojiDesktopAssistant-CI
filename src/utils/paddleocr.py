import os
import time
from typing import Literal

# --- 强行引导 PyInstaller 捞取 chardet 子模块 ---
try:
    import chardet
    import chardet.pipeline
    import chardet.pipeline.orchestrator
except ImportError:
    pass
# ---------------------------------------------

import numpy as np
from PIL import Image

from .assets import AssetOcr
from .log import logger
from .paddle_model import PaddleModel
from .point import Point, Rectangle
from .screenshot import ScreenShot
from .window import window_manager

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"


def check_ocr_folder():
    """检查OCR资源是否存在，不存在则自动下载"""
    return PaddleModel.auto_download(3)


class OCRManager:
    """OCR管理器，负责OCR的初始化、资源管理和清理"""

    def __init__(self):
        self._init: bool = False
        self.paddleocr = None

    def init(self):
        """初始化OCR"""
        if self._init:
            return

        try:
            from paddleocr import PaddleOCR

            logger.info("开始初始化 PaddleOCR v3...")
            # TODO 本地模型路径
            self.paddleocr = PaddleOCR(
                text_detection_model_name="PP-OCRv3_mobile_det",
                text_recognition_model_name="PP-OCRv3_mobile_rec",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
                det_db_unclip_ratio=1.5,
            )
            self._init = True
            logger.info("OCR初始化成功")

        except Exception as e:
            logger.error(f"OCR初始化失败: {e}")
            self._init = False
            raise

    def is_initialized(self) -> bool:
        """检查OCR是否已初始化"""
        return self._init

    def detect(self, image: Image.Image) -> list:
        """执行OCR检测

        Args:
            image: PIL Image 对象

        Returns:
            list: OCR检测结果
        """
        if not self._init:
            if not self.init():
                return []

        try:
            t1 = time.perf_counter()

            img_np = np.array(image)
            t2 = time.perf_counter()
            logger.debug(f"图像转换耗时: {(t2 - t1) * 1000:.2f} ms")

            result = self.paddleocr.predict(input=img_np)
            t3 = time.perf_counter()
            logger.debug(f"OCR预测耗时: {(t3 - t2) * 1000:.2f} ms")
            logger.debug(f"OCR总耗时: {(t3 - t1) * 1000:.2f} ms")

            return result
        except Exception as e:
            logger.error(f"OCR检测失败: {e}")
            return []


# 全局OCR管理器实例
ocr_manager = OCRManager()


def get_ocrdata_from_result(raw_result):
    """从新版 OCR 结果中提取数据

    Args:
        raw_result: 新版 PaddleOCR v5 的结果

    Returns:
        list: 格式化后的结果列表
    """
    rec_texts = raw_result["rec_texts"]
    rec_scores = raw_result["rec_scores"]
    rec_boxes = raw_result["rec_boxes"]
    result_list = []
    for text, score, box in zip(rec_texts, rec_scores, rec_boxes):
        item = {
            "Text": text,
            "Score": score,
            "BoxPoints": [
                {"X": int(box[0]), "Y": int(box[1])},
                {"X": int(box[2]), "Y": int(box[1])},
                {"X": int(box[2]), "Y": int(box[3])},
                {"X": int(box[0]), "Y": int(box[3])},
            ],
        }
        result_list.append(item)
    return result_list


class OcrData:
    text: str
    """识别文本"""
    score: float
    """分数阈值"""
    rect: Rectangle
    """识别区域"""
    center: Point
    """识别区域中心坐标"""

    def __init__(self, item) -> None:
        self.score: float = round(item["Score"], 2)
        self.text: str = item["Text"]
        _BoxPoints = item["BoxPoints"]
        for i in range(len(_BoxPoints)):
            match i:
                case 0:
                    self.x1: int = _BoxPoints[i]["X"]
                    self.y1: int = _BoxPoints[i]["Y"]
                case 2:
                    self.x2: int = _BoxPoints[i]["X"]
                    self.y2: int = _BoxPoints[i]["Y"]
        self.rect = Rectangle(self.x1, self.y1, x2=self.x2, y2=self.y2)
        self.center = self.rect.get_center_point()

    def __repr__(self) -> str:
        return f"text: {self.text}, score: {self.score}, rect: {self.rect.get_box()}, center: {self.center}"


class OcrDetector:
    """OCR检测器，负责执行OCR检测和结果处理"""

    def __init__(self, region: tuple | None = None):
        """
        Args:
            region: 检测区域，格式为 (x, y, width, height)
        """
        self.region = region or window_manager.current.client_rect

    def get_raw_result(self) -> list[OcrData]:
        """获取原始OCR检测结果

        Returns:
            list[OcrData]: OCR检测结果列表
        """
        start_time = time.time()
        screenshot = ScreenShot(rect=self.region)
        image = screenshot.get_image()

        ocr_result = ocr_manager.detect(image)
        data_result: list[OcrData] = []
        try:
            # 处理新版 OCR 结果
            formatted_result = []
            for res in ocr_result:
                formatted_result.extend(get_ocrdata_from_result(res))

            if not isinstance(formatted_result, list):
                logger.error(f"OCR result is not a list: {formatted_result}")
                return data_result
        except Exception as e:
            logger.error(f"Failed to parse OCR result: {str(e)}")
            logger.error(f"Raw OCR result: {ocr_result}")
            return data_result

        for item in formatted_result:
            # 过滤无效数据
            if not isinstance(item, dict):
                logger.warning(f"OCR item is not a dict: {item}")
                continue
            if item.get("Score", 0.0) == 0.0:
                continue
            if item.get("Text", "") == "":
                continue
            ocr_data = OcrData(item)
            logger.info(f"result: {ocr_data}")
            data_result.append(ocr_data)

        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        logger.info(f"OCR detection took {elapsed_ms:.2f} ms")
        return data_result


class RuleOcr:
    """文字识别

    用法1：
    ```python
    ruleocr = RuleOcr(asset)
    if result := ruleocr.match():
        Mouse.click(result.center, *args, **kwargs)
    ```

    用法2：
    ```python
    detector = OcrDetector()
    result = detector.get_raw_result()
    for item in result:
        if target_text in item.text:
            do something

    ```
    """

    def __init__(
        self,
        assetocr: AssetOcr = None,
        name: str = None,
        keyword: str = None,
        region: tuple = None,  # 暂未用上
        score: float = 0.7,
        method: Literal["PERFACT", "INCLUDE"] = "PERFACT",
    ) -> None:
        """
        Args:
            assetocr (AssetOcr):  文字识别资源
            name (str): 名称
            keyword (str): 关键词
            region (tuple): 区域
            score (float): 识别阈值
            method (Literal["PERFACT", "INCLUDE"]): 匹配方式，PERFACT：完全匹配，INCLUDE：包含匹配
        """
        if assetocr:
            self.keyword = assetocr.keyword
            self.name = assetocr.name
            self.region = assetocr.region
            self.score = assetocr.score
            self.method = assetocr.method
        else:
            self.keyword = keyword
            self.name = name
            self.region = region
            self.score = score
            self.method = method

        if self.region is None or self.region == (0, 0, 0, 0):
            self.region = window_manager.current.client_rect

        self.match_result: OcrData = None
        self.detector = OcrDetector(self.region)

    def get_raw_result(self) -> list[OcrData]:
        """获取原始OCR检测结果

        Returns:
            list[OcrData]: OCR检测结果列表
        """
        return self.detector.get_raw_result()

    def match(
        self,
        ocr_result: list[OcrData] = None,
        keyword: str = None,
        score: float = None,
        debug: bool = False,
    ) -> OcrData | None:
        """执行文字匹配

        Args:
            ocr_result: 预计算的OCR结果，如果为None则自动计算
            keyword: 要匹配的关键词，如果为None则使用初始化时的关键词
            score: 匹配阈值，如果为None则使用初始化时的阈值
            debug: 是否开启调试模式

        Returns:
            OcrData | None: 匹配结果
        """
        # 确保OCR已初始化
        if not ocr_manager.is_initialized():
            ocr_manager.init()

        if ocr_result is None:
            ocr_result = self.get_raw_result()

        if keyword is None:
            keyword = self.keyword
        if score is None:
            score = self.score

        for item in ocr_result:
            if item.score < score:
                continue
            if self.method == "PERFACT":
                if item.text == keyword:
                    self.match_result = item
                    return item
            elif self.method == "INCLUDE":
                if keyword in item.text:
                    self.match_result = item
                    return item

        return None


def ocr_match_once(asset_list: list[AssetOcr]) -> RuleOcr | None:
    """文字匹配

    参数:
        asset_list (list[AssetOcr]): 关键字列表

    返回:
        AssetOcr | None: 识别结果
    """
    # 使用OcrDetector获取一次OCR结果，避免重复截图
    detector = OcrDetector()
    ocr_result = detector.get_raw_result()

    for item in asset_list:
        rule = RuleOcr(item)
        result = rule.match(ocr_result)
        if result:
            return rule

    return None
