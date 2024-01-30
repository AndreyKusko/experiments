# CI/CD / CI CD

сделать пайплайны быстрее
https://habr.com/ru/companies/gitlab/articles/646579/


уот тут очень хорошая инструкция

https://www.digitalocean.com/community/tutorials/how-to-set-up-a-continuous-deployment-pipeline-with-gitlab-ci-cd-on-ubuntu-18-04


docker2

    >>> Enter a name for the runner. This is stored only in the local config.toml file:
    docker2 (deployer)
    >>> Enter an executor: virtualbox, docker, docker-autoscaler, instance, custom, shell, ssh, parallels, docker-windows, docker+machine, kubernetes:
    docker
    >>> Enter the default Docker image (for example, ruby:2.7):
    python:3:12

    
    root@2433663-ek93917:~# gitlab-runner register  --url https://gitlab.com  --token glrt-k_fpxNpznLX_TKCSGiXb
    root@2433663-ek93917:~# sudo curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100 61.2M  100 61.2M    0     0  15.6M      0  0:00:03  0:00:03 --:--:-- 15.6M
    root@2433663-ek93917:~# sudo chmod +x /usr/local/bin/gitlab-runner
    root@2433663-ek93917:~# sudo useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
    root@2433663-ek93917:~# sudo gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
    sudo gitlab-runner start
    Runtime platform                                    arch=amd64 os=linux pid=87821 revision=c72a09b6 version=16.8.0
    Runtime platform                                    arch=amd64 os=linux pid=87913 revision=c72a09b6 version=16.8.0
    root@2433663-ek93917:~# gitlab-runner register  --url https://gitlab.com  --token glrt-k_fpxNpznLX_TKCSGiXb
    Runtime platform                                    arch=amd64 os=linux pid=88010 revision=c72a09b6 version=16.8.0
    Running in system-mode.                            
                                                       
    Enter the GitLab instance URL (for example, https://gitlab.com/):
    [https://gitlab.com]: https://gitlab.com/
    Verifying runner... is valid                        runner=k_fpxNpzn
    Enter a name for the runner. This is stored only in the local config.toml file:
    [2433663-ek93917.twc1.net]: docker2
    Enter an executor: virtualbox, docker, docker-autoscaler, instance, custom, shell, ssh, parallels, docker-windows, docker+machine, kubernetes:
    docker
    Enter the default Docker image (for example, ruby:2.7):
    
    Enter the default Docker image (for example, ruby:2.7):
    
    Enter the default Docker image (for example, ruby:2.7):
    python:3:12
    Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded!
     
    Configuration (with the authentication token) was saved in "/etc/gitlab-runner/config.toml" 
    root@2433663-ek93917:~# 
    root@2433663-ek93917:~# 
    root@2433663-ek93917:~# nano etc/gitlab-runner/config.toml
    root@2433663-ek93917:~# 
    root@2433663-ek93917:~# 
    root@2433663-ek93917:~# 
    root@2433663-ek93917:~# gitlab-runner run
    


sudo adduser deployer

kADDLJIIh48tginp3_05gj0in2po2m_0o29j30ri5ngon24o3tg894hn2ioiewnfjdvkiw1fedv_s_dfkl


ssh-keygen -t rsa


sudo usermod -aG docker deployer
usermod -a -G docker deployer
chmod 666 /var/run/docker.sock
chown deployer /var/run/docker.sock
![Снимок экрана 2024-01-22 в 01.27.08.png](..%2F..%2F..%2F..%2F..%2F..%2Fvar%2Ffolders%2Fbs%2Fwftf_ccj2nd5b_zckjh7g0_c0000gn%2FT%2FTemporaryItems%2FNSIRD_screencaptureui_jBHDdL%2F%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202024-01-22%20%D0%B2%2001.27.08.png)



nginx 

    https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/


connect to postgres
    
    find / -name "postgresql.conf"

    /etc/postgresql/14/main/postgresql.conf
    /etc/postgresql/13/main/postgresql.conf
    set falue 
    listen_addresses = '*'          # what IP address(es) to listen on;
    
    nano /etc/postgresql/14/main/pg_hba.conf
    nano /etc/postgresql/13/main/pg_hba.conf
    host    all             all             0.0.0.0/0               md5
    host    all             all             127.0.0.1/16            scram-sha-256
    
    
[//]: # (    sudo service postgresql restart)
[//]: # (    sudo systemctl restart postgresql)
    systemctl restart postgresql
    systemctl restart postgresql-9.3
    /etc/init.d/postgresql restart

gitlab runner

go to file

    nano /etc/gitlab-runner/config.toml

set is priveleged true

    concurrent = 1
    check_interval = 0
    shutdown_timeout = 0
    
    [session_server]
      session_timeout = 1800
    
    [[runners]]
      name = "docker2"
      url = "https://gitlab.com/"
      id = 31792830
      token = "glrt-k_fpxNpznLX_TKCSGiXb"
      token_obtained_at = 2024-01-21T20:16:39Z
      token_expires_at = 0001-01-01T00:00:00Z
      executor = "docker"
      [runners.cache]
        MaxUploadedArchiveSize = 0
      [runners.docker]
        tls_verify = false
        image = "python:3:12"
        privileged = true
        disable_entrypoint_overwrite = false
        oom_kill_disable = false
        disable_cache = false
        volumes = ["/cache"]
        shm_size = 0
        network_mtu = 0
    


restart gitlab runner 
    
    gitlab-runner restart

    https://docs.gitlab.com/runner/commands/
    
Если валится докер ошибкой

    OS/Arch:Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?

то нужно открыть права на файл

    root@shushundr:/etc/gitlab-runner# sudo chown root:docker /var/run/docker.sock
    root@shushundr:/etc/gitlab-runner# sudo chown deployer:docker /var/run/docker.sock
    root@shushundr:/etc/gitlab-runner# sudo chmod 660 /var/run/docker.sock


