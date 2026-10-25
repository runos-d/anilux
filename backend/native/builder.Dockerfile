ARG BACKEND_IMAGE=anilux-backend:local-release
FROM node:22-bookworm-slim@sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d AS node
FROM ${BACKEND_IMAGE}
ARG DEBIAN_FRONTEND=noninteractive
ENV container=docker
USER root
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
RUN sed -i '\|path-exclude.*/usr/share/man|d' /etc/dpkg/dpkg.cfg.d/docker \
    && apt-get -o Acquire::Retries=3 -o APT::Update::Error-Mode=any update \
    && apt-get install -y --no-install-recommends openjdk-21-jdk-headless curl unzip xz-utils fakeroot rpm squashfs-tools flatpak flatpak-builder elfutils binutils ostree \
    && rm -rf /var/lib/apt/lists/*
ENV ANDROID_HOME=/opt/android-sdk JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="/opt/gradle/bin:/opt/android-sdk/cmdline-tools/latest/bin:${PATH}"
ADD --checksum=sha256:4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583 https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip /tmp/android.zip
RUN mkdir -p /opt/android-sdk/cmdline-tools && unzip -q /tmp/android.zip -d /opt/android-sdk/cmdline-tools && mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest && rm /tmp/android.zip
ADD --checksum=sha256:f397b287023acdba1e9f6fc5ea72d22dd63669d59ed4a289a29b1a76eee151c6 https://services.gradle.org/distributions/gradle-8.11.1-bin.zip /tmp/gradle.zip
RUN unzip -q /tmp/gradle.zip -d /opt && mv /opt/gradle-8.11.1 /opt/gradle && rm /tmp/gradle.zip
RUN yes | android --no-metrics --sdk=/opt/android-sdk sdk install 'platform-tools' \
    && yes | android --no-metrics --sdk=/opt/android-sdk sdk install 'build-tools;35.0.0' \
    && yes | android --no-metrics --sdk=/opt/android-sdk sdk install 'platforms;android-35' \
    && chown -R appuser:appuser /opt/android-sdk
RUN apt-get -o Acquire::Retries=3 -o APT::Update::Error-Mode=any update && apt-get install -y --no-install-recommends mono-mcs libmono-system-windows-forms4.0-cil libmono-system-web-extensions4.0-cil nsis && rm -rf /var/lib/apt/lists/*
COPY --chown=appuser:appuser . /app
RUN mkdir -p /app/data/native_cache && chown appuser:appuser /app/data/native_cache
USER appuser
CMD ["celery", "-A", "config", "worker", "-Q", "native_builds", "-l", "info", "--concurrency=1", "--prefetch-multiplier=1", "--hostname=native-apps@%h"]
