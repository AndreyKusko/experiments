  broadcastserv:
    image: cr.yandex/crp410gd0ii2flvgdi8s/broadcastserv:latest
    restart: on-failure
    command: >
      bash -c "uvicorn main.asgi:app --proxy-headers --host 0.0.0.0 --port 8011"
    ports:
      - "8011:8011"
    volumes:
      - "/opt/root.crt:/usr/src/broadcastserv/root.crt"
    environment:
        SENTRY_URL: https://07514c088d6c4e8e867fbf3ff334ae77@sentry.millionagents.com/9
        SERVER_ENVIRONMENT: common
        BROADCAST_REDIS_URI: redis://redis:6379/10
        TRUST_TOKEN: lwkefo9i24309t5i23g5n024i50nfri0234
        POLICY_REDIS_URI: redis://redis:6379/4
        DEBUG: 1
        KAFKA_URI_BROADCAST: "kafka://ma:MH38iGXq7pcMCUf@kafka.ma.works:8092?topic=madirect.broadcast&sasl_mechanism=PLAIN&security_protocol=SASL_PLAINTEXT"

  websocketserv:
    image: cr.yandex/crp410gd0ii2flvgdi8s/websocketserv:latest
    restart: on-failure
    command: >
      bash -c "uvicorn main.asgi:app --proxy-headers --host 0.0.0.0 --port 8012"
    ports:
      - "8012:8012"
    depends_on:
        - broadcastserv
    volumes:
      - "/opt/root.crt:/usr/src/websocketserv/root.crt"
    environment:
        SENTRY_URL: https://07514c088d6c4e8e867fbf3ff334ae77@sentry.millionagents.com/9
        SERVER_ENVIRONMENT: common
        BROADCAST_REDIS_URI_DEV: redis://redis:6379/10
        BROADCAST_SERVICE_LINK: http://broadcastserv:8011?TRUST_TOKEN=lwkefo9i24309t5i23g5n024i50nfri0234
        DEBUG: 1
        BROADCAST_REDIS_URI_STAGE: redis://redis:6379/2 # redis://192.168.1.5:6379/2
        BROADCAST_REDIS_URI_PROD: redis://redis:6379/??? # redis://192.168.1.5:6379/2

