import os
import tarfile
from enum import Enum

import requests

from .log import logger


class ModelType(Enum):
    DET = "det"
    REC = "rec"


class PaddleModel:
    name: str = ""
    version: int = 0
    model_type: ModelType = None
    base_url: str = "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/"

    @property
    def url(self) -> str:
        return f"{self.base_url}{self.name}_infer.tar"

    @classmethod
    def download_version(cls, version: int) -> None:
        """下载指定版本的det和rec模型到当前目录的model文件夹"""
        # 创建model文件夹
        model_dir = os.path.join(os.getcwd(), "model")
        os.makedirs(model_dir, exist_ok=True)

        # 确定要下载的模型类
        det_class = None
        rec_class = None

        for subclass in cls.__subclasses__():
            if subclass.version == version:
                if subclass.model_type == ModelType.DET:
                    det_class = subclass
                elif subclass.model_type == ModelType.REC:
                    rec_class = subclass

        if not det_class or not rec_class:
            logger.ui_warn(f"未找到版本 {version} 的模型")
            return

        # 下载det模型
        det_model = det_class()
        det_file = os.path.join(model_dir, f"{det_model.name}_infer.tar")
        logger.ui(f"下载 {det_model.name} 模型...")
        cls._download_file(det_model.url, det_file)
        cls._extract_tar(det_file, model_dir)

        # 下载rec模型
        rec_model = rec_class()
        rec_file = os.path.join(model_dir, f"{rec_model.name}_infer.tar")
        logger.ui(f"下载 {rec_model.name} 模型...")
        cls._download_file(rec_model.url, rec_file)
        cls._extract_tar(rec_file, model_dir)

        logger.ui(f"版本 {version} 的模型下载完成")

    @staticmethod
    def _download_file(url: str, save_path: str) -> None:
        """下载文件（带进度条）"""

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        last_logged_percent = 0

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # 计算并显示进度（每10%输出一次）
                    if total_size > 0:
                        progress = downloaded_size / total_size * 100
                        current_percent = int(progress // 10 * 10)
                        if current_percent != last_logged_percent and current_percent % 10 == 0:
                            last_logged_percent = current_percent
                            logger.ui(
                                f"下载进度: {progress:.1f}% ({downloaded_size / 1024 / 1024:.2f}MB/{total_size / 1024 / 1024:.2f}MB)"
                            )

    @staticmethod
    def _extract_tar(tar_path: str, extract_dir: str) -> None:
        """解压tar文件"""
        logger.info(f"开始解压文件: {os.path.basename(tar_path)}")
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(extract_dir)
        # 删除tar文件
        os.remove(tar_path)
        logger.info(f"解压完成: {os.path.basename(tar_path)}")

    @classmethod
    def check_model_files(cls, version: int) -> bool:
        """检测指定版本的模型文件是否完整"""
        # 检查model文件夹是否存在
        model_dir = os.path.join(os.getcwd(), "model")
        if not os.path.exists(model_dir):
            logger.error("model文件夹不存在")
            return False

        # 确定要检查的模型类
        det_class = None
        rec_class = None

        for subclass in cls.__subclasses__():
            if subclass.version == version:
                if subclass.model_type == ModelType.DET:
                    det_class = subclass
                elif subclass.model_type == ModelType.REC:
                    rec_class = subclass

        if not det_class or not rec_class:
            logger.ui_warn(f"未找到版本 {version} 的模型")
            return False

        # 检查det模型文件
        det_model = det_class()
        det_model_dir = os.path.join(model_dir, f"{det_model.name}_infer")
        if not os.path.exists(det_model_dir):
            logger.ui_error(f"{det_model.name}_infer 目录不存在")
            return False

        # 检查必要的文件
        required_files = ["inference.json", "inference.pdiparams", "inference.yml"]

        for file_name in required_files:
            file_path = os.path.join(det_model_dir, file_name)
            if not os.path.exists(file_path):
                logger.ui_error(f"{det_model.name}_infer 缺少文件: {file_name}")
                return False

        # 检查rec模型文件
        rec_model = rec_class()
        rec_model_dir = os.path.join(model_dir, f"{rec_model.name}_infer")
        if not os.path.exists(rec_model_dir):
            logger.ui_error(f"{rec_model.name}_infer 目录不存在")
            return False

        for file_name in required_files:
            file_path = os.path.join(rec_model_dir, file_name)
            if not os.path.exists(file_path):
                logger.ui_error(f"{rec_model.name}_infer 缺少文件: {file_name}")
                return False

        logger.ui(f"PP-OCRv{version} 的模型文件完整")
        return True

    @classmethod
    def auto_download(cls, version: int) -> bool:
        """自动检查并下载指定版本的模型"""
        logger.info(f"检查 PP-OCRv{version} 的模型文件...")

        # 检查模型是否完整
        if cls.check_model_files(version):
            logger.info("模型已存在且完整，无需下载")
            return True

        # 模型不完整或不存在，开始下载
        logger.ui(f"模型不完整或不存在，开始下载 PP-OCRv{version} 的模型...")
        cls.download_version(version)

        # 再次检查模型是否完整
        logger.info(f"下载完成，检查 PP-OCRv{version} 的模型文件...")
        return cls.check_model_files(version)


class OCRv5MobileDet(PaddleModel):
    name: str = "PP-OCRv5_mobile_det"
    version: int = 5
    model_type: ModelType = ModelType.DET


class OCRv5MobileRec(PaddleModel):
    name: str = "PP-OCRv5_mobile_rec"
    version: int = 5
    model_type: ModelType = ModelType.REC


class OCRv4MobileDet(PaddleModel):
    name: str = "PP-OCRv4_mobile_det"
    version: int = 4
    model_type: ModelType = ModelType.DET


class OCRv4MobileRec(PaddleModel):
    name: str = "PP-OCRv4_mobile_rec"
    version: int = 4
    model_type: ModelType = ModelType.REC


class OCRv3MobileDet(PaddleModel):
    name: str = "PP-OCRv3_mobile_det"
    version: int = 3
    model_type: ModelType = ModelType.DET


class OCRv3MobileRec(PaddleModel):
    name: str = "PP-OCRv3_mobile_rec"
    version: int = 3
    model_type: ModelType = ModelType.REC
