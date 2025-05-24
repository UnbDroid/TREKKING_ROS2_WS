# Usa a imagem oficial do Ubuntu 24.04 como base
FROM ubuntu:24.04

# Evita perguntas interativas durante a instalação de pacotes
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt upgrade && apt install software-properties-common -y && add-apt-repository universe -y

# Atualiza o sistema e instala dependências básicas
RUN apt-get update && apt-get install -y \
    locales \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configura o locale
RUN locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

# Adiciona o repositório do ROS 2
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Instala o ROS 2 Jazzy Desktop
RUN apt-get update && apt-get install -y ros-dev-tools ros-jazzy-desktop ros-jazzy-nav2-bringup ros-jazzy-ament* && rm -rf /var/lib/apt/lists/*

# Inicializa o rosdep
RUN rosdep init && rosdep update

# Cria um usuário não-root chamado 'droid_user'
RUN groupadd --gid 20 dialout || true && \
    useradd -m -s /bin/bash -u 1001 -g users -G dialout,sudo droid_user && \
    echo "droid_user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Define o diretório de trabalho para os projetos e copia o workspace
USER droid_user
WORKDIR /home/droid_user/Projects/DROID
COPY --chown=droid_user:droid_user . ./TREKKING_ROS2_WS
WORKDIR /home/droid_user/Projects/DROID/TREKKING_ROS2_WS

# Seta o shell para bash
SHELL ["/bin/bash", "-c"]

# Seta o ambiente do ROS 2
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Instala dependências do workspace e compila
RUN source /opt/ros/jazzy/setup.bash && rosdep update && \
    rosdep install -i --from-path src --rosdistro jazzy --skip-keys "cmake_modules" -y && \
    colcon build --symlink-install

# Define o diretório de trabalho final
WORKDIR /home/droid_user

# Comando padrão ao iniciar o container
CMD ["bash"]

