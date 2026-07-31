# ========== Stage 1: 构建依赖层 ==========
FROM python:3.11-slim-bookworm AS builder

# 使用阿里云 PyPI 镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.aliyun.com

WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt ./

# 安装依赖到独立目录，便于后续复制
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ========== Stage 2: 运行时镜像 ==========
FROM python:3.11-slim-bookworm

LABEL maintainer="haoshenqitop@163.com"

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖：
# - calibre 提供 ebook-convert / calibredb 等转换与元数据工具
# - libmagic1 + ghostscript + imagemagick 支持书籍封面/格式转换
# - netcat-openbsd 用于 entrypoint 等待检查
# - tini 作为 init 进程，正确处理信号
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
        gosu \
        netcat-openbsd \
        libmagic1 \
        ghostscript \
        imagemagick \
        calibre \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制已安装的 Python 依赖
COPY --from=builder /install /usr/local

WORKDIR /app

# 复制应用代码
COPY . .

# 创建非 root 用户运行（UID/GID 可在 compose 中通过 user 指定覆盖）
RUN groupadd -r calibre && useradd -r -g calibre -d /app -s /sbin/nologin calibre \
    && mkdir -p /calibre-library /config /app/logs \
    && chown -R calibre:calibre /app /calibre-library /config

USER calibre

# 环境变量默认值
ENV CALIBRE_PORT=8083 \
    CALIBRE_DBPATH=/config \
    CALIBRE_LIBRARY=/calibre-library \
    PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8083

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD nc -z localhost 8083 || exit 1

# 使用 tini 作为 init 进程，正确转发信号给 Python
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
