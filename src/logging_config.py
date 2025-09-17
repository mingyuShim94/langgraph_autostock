"""
LV1 Observer - 로깅 시스템 설정
"""
import logging
import os
from datetime import datetime
from config.settings import settings

def setup_logging():
    """로깅 시스템을 설정합니다."""

    # logs 디렉토리가 없으면 생성
    os.makedirs("logs", exist_ok=True)

    # 로그 레벨 설정
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 로그 포맷 설정
    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (일별 로그 파일)
    today = datetime.now().strftime('%Y%m%d')
    log_filename = f"logs/observer_{today}.log"

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 에러 전용 파일 핸들러
    error_filename = f"logs/observer_error_{today}.log"
    error_handler = logging.FileHandler(error_filename, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    logging.info("로깅 시스템이 초기화되었습니다.")
    logging.info(f"로그 레벨: {settings.LOG_LEVEL}")
    logging.info(f"로그 파일: {log_filename}")

    return logger

# 모듈 전역 로거
logger = logging.getLogger(__name__)