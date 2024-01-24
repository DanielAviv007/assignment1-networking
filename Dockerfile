FROM alpine:latest
RUN apk update && apk add iproute2 python3 tcpdump
CMD ["sh"]
