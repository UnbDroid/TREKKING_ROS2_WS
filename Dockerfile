# Usa a imagem oficial OSRF ROS 2 Jazzy Desktop Full como base
FROM osrf/ros:jazzy-desktop-full

# Evita perguntas interativas durante a instalação de pacotes
ENV DEBIAN_FRONTEND=noninteractive

# Instala git e atualiza rosdep.
# A imagem base já deve ter rosdep inicializado.
USER root
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN rosdep update

# Cria um usuário não-root chamado 'droid_user'
# Adiciona ao grupo 'dialout' para acesso a dispositivos seriais/USB
# Adiciona ao grupo 'sudo' para conveniência (ex: rodar rosdep install que usa apt)
RUN groupadd --gid 20 dialout || true \
    && useradd -m -s /bin/bash -u 1001 -g users -G dialout,sudo droid_user \
    && echo "droid_user:droid_user" | chpasswd

# Muda para o usuário não-root
USER droid_user
WORKDIR /home/droid_user

# Define o diretório de trabalho para os projetos e copia o workspace
RUN mkdir -p Projects/DROID
WORKDIR /home/droid_user/Projects/DROID

COPY --chown=droid_user:droid_user . ./TREKKING_ROS2_WS
WORKDIR /home/droid_user/Projects/DROID/TREKKING_ROS2_WS

# Instala dependências do workspace e compila
# rosdep install precisa de privilégios para instalar pacotes do sistema (apt)
# Como droid_user está no sudo e tem senha, ele pode executar.
# Se o sudo pedir senha interativamente e falhar no build:
#   Opção 1: Rodar essas linhas como USER root e depois dar chown nos arquivos gerados.
#   Opção 2: Configurar sudo para não pedir senha para droid_user (mais complexo no Dockerfile).
# Vamos tentar direto, pois o droid_user está no sudo.
# O --rosdistro jazzy é importante para o rosdep.
RUN rosdep install --from-paths src -y --ignore-src --rosdistro jazzy && \
    colcon build --symlink-install

# O ENTRYPOINT da imagem base (/ros_entrypoint.sh) já faz o source de /opt/ros/jazzy/setup.bash
# Nosso CMD vai sourçar o setup do workspace local e então executar o launch file.
CMD ["bash", "-c", "source install/setup.bash && ros2 launch trekking main.launch.py"]
