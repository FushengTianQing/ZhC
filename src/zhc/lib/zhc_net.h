/**
 * zhc_net.h - 网络库
 *
 * 提供 Socket 编程和 HTTP 客户端功能：
 * - TCP Socket 客户端/服务器
 * - UDP Socket
 * - HTTP GET/POST 客户端
 * - URL 解析
 * - DNS 解析
 *
 * 版本: 1.0
 * 依赖: <sys/socket.h>, <netinet/in.h>, <arpa/inet.h>, <netdb.h>, <unistd.h>
 */

#ifndef ZHC_NET_H
#define ZHC_NET_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 常量定义
 * ================================================================ */

/** 地址族 - Unix 域 */
#define ZHC_AF_UNIX   1
/** 地址族 - IPv4 */
#define ZHC_AF_INET   2
/** 地址族 - IPv6 */
#define ZHC_AF_INET6  10

/** 协议 - TCP */
#define ZHC_IPPROTO_TCP 6
/** 协议 - UDP */
#define ZHC_IPPROTO_UDP 17

/** 无效套接字 */
#define ZHC_INVALID_SOCKET -1

/* ================================================================
 * 类型定义
 * ================================================================ */

/**
 * 地址结构
 */
typedef struct {
    char host[256];   /* 主机名或 IP */
    int port;         /* 端口号 */
    int family;       /* 地址族 */
} zhc_addr_t;

/**
 * URL 结构
 */
typedef struct {
    char protocol[32];  /* 协议 (http/https) */
    char host[256];     /* 主机 */
    int port;           /* 端口 */
    char path[1024];    /* 路径 */
    char query[1024];   /* 查询参数 */
} zhc_url_t;

/**
 * HTTP 响应结构
 */
typedef struct {
    int status_code;       /* HTTP 状态码 */
    char* status_text;     /* 状态文本 */
    char* headers;         /* 原始头信息 */
    char* content_type;    /* 内容类型 */
    char* content;         /* 响应内容 */
    int content_length;    /* 内容长度 */
} zhc_http_response_t;

/* ================================================================
 * TCP Socket 函数
 * ================================================================ */

/**
 * zhc_tcp_socket - 创建 TCP 套接字
 *
 * 返回: 套接字描述符，-1 表示失败
 */
int zhc_tcp_socket(void);

/**
 * zhc_tcp_connect - 连接到服务器
 *
 * 参数:
 *   host - 服务器主机名或 IP
 *   port - 端口号
 *
 * 返回: 套接字描述符，-1 表示失败
 */
int zhc_tcp_connect(const char* host, int port);

/**
 * zhc_tcp_bind - 绑定端口
 *
 * 参数:
 *   sock  - 套接字描述符
 *   port  - 端口号
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_tcp_bind(int sock, int port);

/**
 * zhc_tcp_listen - 开始监听
 *
 * 参数:
 *   sock    - 套接字描述符
 *   backlog - 最大连接队列长度
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_tcp_listen(int sock, int backlog);

/**
 * zhc_tcp_accept - 接受连接
 *
 * 参数:
 *   sock        - 监听套接字
 *   client_ip   - 客户端 IP 输出缓冲区（可为 NULL）
 *   client_port - 客户端端口输出（可为 NULL）
 *
 * 返回: 客户端套接字，-1 表示失败
 */
int zhc_tcp_accept(int sock, char* client_ip, int* client_port);

/**
 * zhc_tcp_send - 发送数据
 *
 * 参数:
 *   sock - 套接字描述符
 *   data - 数据指针
 *   len  - 数据长度
 *
 * 返回: 发送的字节数，-1 表示失败
 */
int zhc_tcp_send(int sock, const char* data, size_t len);

/**
 * zhc_tcp_recv - 接收数据
 *
 * 参数:
 *   sock   - 套接字描述符
 *   buffer - 接收缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: 接收的字节数，0 表示连接关闭，-1 表示错误
 */
int zhc_tcp_recv(int sock, char* buffer, size_t size);

/**
 * zhc_tcp_set_timeout - 设置超时
 *
 * 参数:
 *   sock       - 套接字描述符
 *   timeout_ms - 超时时间（毫秒）
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_tcp_set_timeout(int sock, int timeout_ms);

/**
 * zhc_tcp_close - 关闭套接字
 *
 * 参数:
 *   sock - 套接字描述符
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_tcp_close(int sock);

/* ================================================================
 * UDP Socket 函数
 * ================================================================ */

/**
 * zhc_udp_socket - 创建 UDP 套接字
 *
 * 返回: 套接字描述符，-1 表示失败
 */
int zhc_udp_socket(void);

/**
 * zhc_udp_bind - 绑定端口
 *
 * 参数:
 *   sock - 套接字描述符
 *   port - 端口号
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_udp_bind(int sock, int port);

/**
 * zhc_udp_sendto - 发送数据
 *
 * 参数:
 *   sock       - 套接字描述符
 *   data       - 数据指针
 *   len        - 数据长度
 *   dest_host  - 目标主机
 *   dest_port  - 目标端口
 *
 * 返回: 发送的字节数，-1 表示失败
 */
int zhc_udp_sendto(int sock, const char* data, size_t len,
                   const char* dest_host, int dest_port);

/**
 * zhc_udp_recvfrom - 接收数据
 *
 * 参数:
 *   sock      - 套接字描述符
 *   buffer    - 接收缓冲区
 *   size      - 缓冲区大小
 *   src_host  - 源主机输出（可为 NULL）
 *   src_port  - 源端口输出（可为 NULL）
 *
 * 返回: 接收的字节数，-1 表示错误
 */
int zhc_udp_recvfrom(int sock, char* buffer, size_t size,
                     char* src_host, int* src_port);

/**
 * zhc_udp_close - 关闭 UDP 套接字
 *
 * 参数:
 *   sock - 套接字描述符
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_udp_close(int sock);

/* ================================================================
 * HTTP 函数
 * ================================================================ */

/**
 * zhc_http_get - HTTP GET 请求
 *
 * 注意: 仅支持 HTTP，不支持 HTTPS
 *
 * 参数:
 *   url - 请求 URL
 *
 * 返回: HTTP 响应结构（使用后需调用 zhc_http_response_free 释放）
 *       NULL 表示失败
 */
zhc_http_response_t* zhc_http_get(const char* url);

/**
 * zhc_http_post - HTTP POST 请求
 *
 * 注意: 仅支持 HTTP，不支持 HTTPS
 *
 * 参数:
 *   url          - 请求 URL
 *   data         - POST 数据
 *   content_type - 内容类型（如 "application/json"）
 *
 * 返回: HTTP 响应结构（使用后需调用 zhc_http_response_free 释放）
 *       NULL 表示失败
 */
zhc_http_response_t* zhc_http_post(const char* url, const char* data,
                                    const char* content_type);

/**
 * zhc_http_response_free - 释放 HTTP 响应
 *
 * 参数:
 *   resp - HTTP 响应结构指针
 */
void zhc_http_response_free(zhc_http_response_t* resp);

/* ================================================================
 * URL 函数
 * ================================================================ */

/**
 * zhc_url_parse - 解析 URL
 *
 * 参数:
 *   url    - 输入 URL
 *   result - 解析结果输出
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_url_parse(const char* url, zhc_url_t* result);

/* ================================================================
 * DNS 函数
 * ================================================================ */

/**
 * zhc_get_local_ip - 获取本地 IP 地址
 *
 * 返回: IP 地址字符串（静态内存，需尽快使用）
 *       NULL 表示失败
 */
const char* zhc_get_local_ip(void);

/**
 * zhc_resolve_host - DNS 解析（主机名转 IP）
 *
 * 参数:
 *   hostname - 主机名
 *
 * 返回: IP 地址字符串（静态内存，需尽快使用）
 *       NULL 表示失败
 */
const char* zhc_resolve_host(const char* hostname);

/* ================================================================
 * 实现
 * ================================================================ */

#ifdef ZHC_NET_IMPLEMENTATION

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <stdarg.h>
#include <time.h>

/* ---------- TCP 实现 ---------- */

int zhc_tcp_socket(void) {
    return socket(AF_INET, SOCK_STREAM, 0);
}

int zhc_tcp_connect(const char* host, int port) {
    struct hostent* he;
    struct sockaddr_in addr;
    int sock;

    he = gethostbyname(host);
    if (he == NULL) {
        return -1;
    }

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    memcpy(&addr.sin_addr, he->h_addr_list[0], (size_t)he->h_length);

    if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(sock);
        return -1;
    }

    return sock;
}

int zhc_tcp_bind(int sock, int port) {
    struct sockaddr_in addr;
    int opt = 1;

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((uint16_t)port);

    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    return bind(sock, (struct sockaddr*)&addr, sizeof(addr));
}

int zhc_tcp_listen(int sock, int backlog) {
    return listen(sock, backlog);
}

int zhc_tcp_accept(int sock, char* client_ip, int* client_port) {
    struct sockaddr_in client;
    socklen_t addrlen = sizeof(client);

    int client_sock = accept(sock, (struct sockaddr*)&client, &addrlen);
    if (client_sock < 0) {
        return -1;
    }

    if (client_ip) {
        inet_ntop(AF_INET, &client.sin_addr, client_ip, INET_ADDRSTRLEN);
    }
    if (client_port) {
        *client_port = (int)ntohs(client.sin_port);
    }

    return client_sock;
}

int zhc_tcp_send(int sock, const char* data, size_t len) {
    return (int)send(sock, data, len, 0);
}

int zhc_tcp_recv(int sock, char* buffer, size_t size) {
    return (int)recv(sock, buffer, size, 0);
}

int zhc_tcp_set_timeout(int sock, int timeout_ms) {
    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    return 0;
}

int zhc_tcp_close(int sock) {
    return close(sock);
}

/* ---------- UDP 实现 ---------- */

int zhc_udp_socket(void) {
    return socket(AF_INET, SOCK_DGRAM, 0);
}

int zhc_udp_bind(int sock, int port) {
    struct sockaddr_in addr;
    int opt = 1;

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((uint16_t)port);

    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    return bind(sock, (struct sockaddr*)&addr, sizeof(addr));
}

int zhc_udp_sendto(int sock, const char* data, size_t len,
                   const char* dest_host, int dest_port) {
    struct hostent* he;
    struct sockaddr_in addr;

    he = gethostbyname(dest_host);
    if (he == NULL) {
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)dest_port);
    memcpy(&addr.sin_addr, he->h_addr_list[0], (size_t)he->h_length);

    return (int)sendto(sock, data, len, 0, (struct sockaddr*)&addr, sizeof(addr));
}

int zhc_udp_recvfrom(int sock, char* buffer, size_t size,
                     char* src_host, int* src_port) {
    struct sockaddr_in src;
    socklen_t addrlen = sizeof(src);

    int n = (int)recvfrom(sock, buffer, size, 0, (struct sockaddr*)&src, &addrlen);
    if (n < 0) {
        return -1;
    }

    if (src_host) {
        inet_ntop(AF_INET, &src.sin_addr, src_host, INET_ADDRSTRLEN);
    }
    if (src_port) {
        *src_port = (int)ntohs(src.sin_port);
    }

    return n;
}

int zhc_udp_close(int sock) {
    return close(sock);
}

/* ---------- HTTP 实现 ---------- */

int zhc_url_parse(const char* url, zhc_url_t* result) {
    const char* p = url;
    const char* end;

    if (result == NULL) {
        return -1;
    }
    memset(result, 0, sizeof(zhc_url_t));

    /* 协议 */
    end = strstr(p, "://");
    if (end) {
        size_t proto_len = (size_t)(end - p);
        if (proto_len >= sizeof(result->protocol)) {
            proto_len = sizeof(result->protocol) - 1;
        }
        strncpy(result->protocol, p, proto_len);
        result->protocol[proto_len] = '\0';
        p = end + 3;
    } else {
        strcpy(result->protocol, "http");
    }

    /* 主机和端口 */
    const char* path_start = strchr(p, '/');
    const char* port_start = strchr(p, ':');
    const char* query_start = strchr(p, '?');

    /* 确定主机范围 */
    const char* host_end = path_start;
    if (port_start && (!host_end || port_start < host_end)) {
        host_end = port_start;
    }
    if (query_start && (!host_end || query_start < host_end)) {
        host_end = query_start;
    }

    if (host_end) {
        size_t host_len = (size_t)(host_end - p);
        if (host_len >= sizeof(result->host)) {
            host_len = sizeof(result->host) - 1;
        }
        strncpy(result->host, p, host_len);
        result->host[host_len] = '\0';
    } else {
        strncpy(result->host, p, sizeof(result->host) - 1);
    }

    /* 端口 */
    if (port_start) {
        const char* ps = port_start + 1;
        int port_len = 0;
        while (*ps >= '0' && *ps <= '9' && port_len < 10) {
            port_len++;
            ps++;
        }
        char port_str[16];
        strncpy(port_str, port_start + 1, (size_t)port_len);
        port_str[port_len] = '\0';
        result->port = atoi(port_str);
    } else {
        result->port = (strcmp(result->protocol, "https") == 0) ? 443 : 80;
    }

    /* 路径 */
    if (path_start) {
        size_t path_len = strlen(path_start);
        if (path_len >= sizeof(result->path)) {
            path_len = sizeof(result->path) - 1;
        }
        strncpy(result->path, path_start, path_len);
        result->path[path_len] = '\0';
    } else {
        strcpy(result->path, "/");
    }

    /* 查询参数 */
    if (query_start) {
        size_t query_len = strlen(query_start);
        if (query_len >= sizeof(result->query)) {
            query_len = sizeof(result->query) - 1;
        }
        strncpy(result->query, query_start, query_len);
        result->query[query_len] = '\0';
    }

    return 0;
}

zhc_http_response_t* zhc_http_get(const char* url) {
    zhc_url_t parsed;
    if (zhc_url_parse(url, &parsed) != 0) {
        return NULL;
    }

    if (strcmp(parsed.protocol, "https") == 0) {
        /* 不支持 HTTPS */
        return NULL;
    }

    int sock = zhc_tcp_connect(parsed.host, parsed.port);
    if (sock < 0) {
        return NULL;
    }

    /* 构造 HTTP 请求 */
    char request[4096];
    int req_len = snprintf(request, sizeof(request),
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Connection: close\r\n"
        "User-Agent: ZHC-NET/1.0\r\n"
        "\r\n",
        parsed.path, parsed.host);

    if (zhc_tcp_send(sock, request, (size_t)req_len) != req_len) {
        zhc_tcp_close(sock);
        return NULL;
    }

    /* 接收响应 */
    char* response = NULL;
    size_t response_capacity = 0;
    size_t response_len = 0;
    char recv_buf[4096];
    int n;

    zhc_tcp_set_timeout(sock, 10000);  /* 10 秒超时 */

    while ((n = zhc_tcp_recv(sock, recv_buf, sizeof(recv_buf) - 1)) > 0) {
        if (response_len + (size_t)n + 1 > response_capacity) {
            response_capacity = response_len + (size_t)n + 4096;
            response = realloc(response, response_capacity);
            if (!response) {
                zhc_tcp_close(sock);
                return NULL;
            }
        }
        memcpy(response + response_len, recv_buf, (size_t)n);
        response_len += (size_t)n;
    }
    zhc_tcp_close(sock);

    if (!response || response_len == 0) {
        free(response);
        return NULL;
    }
    response[response_len] = '\0';

    /* 解析 HTTP 响应 */
    zhc_http_response_t* resp = calloc(1, sizeof(zhc_http_response_t));
    if (!resp) {
        free(response);
        return NULL;
    }

    /* 找到 header 和 body 的分界线 */
    char* header_end = strstr(response, "\r\n\r\n");
    if (header_end) {
        *header_end = '\0';
        char* body = header_end + 4;

        /* 解析状态行 */
        char status_line[256];
        strncpy(status_line, response, sizeof(status_line) - 1);
        status_line[sizeof(status_line) - 1] = '\0';

        char* line = status_line;
        while (*line == ' ') line++;
        char* version_end = strchr(line, ' ');
        if (version_end) {
            char* status_start = version_end + 1;
            char* status_end = strchr(status_start, ' ');
            if (status_end) {
                *status_end = '\0';
            }
            resp->status_code = atoi(status_start);
            if (status_end) {
                char* text_start = status_end + 1;
                while (*text_start == ' ') text_start++;
                char* text_end = text_start + strlen(text_start) - 1;
                while (text_end > text_start && (*text_end == '\r' || *text_end == '\n')) {
                    *text_end = '\0';
                }
                resp->status_text = strdup(text_start);
            }
        }

        resp->headers = strdup(response);

        /* 解析 Content-Length */
        char* cl = strstr(response, "Content-Length:");
        if (cl) {
            cl += 14;
            while (*cl == ' ' || *cl == '\t') cl++;
            char* cl_end = strchr(cl, '\r');
            if (cl_end) *cl_end = '\0';
            resp->content_length = atoi(cl);
        } else {
            resp->content_length = (int)strlen(body);
        }

        resp->content = strdup(body);

        /* 解析 Content-Type */
        char* ct = strstr(response, "Content-Type:");
        if (ct) {
            ct += 13;
            while (*ct == ' ' || *ct == '\t') ct++;
            char* ct_end = strchr(ct, '\r');
            if (ct_end) *ct_end = '\0';
            /* 去掉分号后面的内容 */
            char* semi = strchr(ct, ';');
            if (semi) *semi = '\0';
            while (ct[strlen(ct) - 1] == ' ') ct[strlen(ct) - 1] = '\0';
            resp->content_type = strdup(ct);
        }
    } else {
        /* 无法解析响应格式 */
        resp->status_code = 0;
        resp->content = strdup(response);
        resp->content_length = (int)strlen(response);
    }

    free(response);
    return resp;
}

zhc_http_response_t* zhc_http_post(const char* url, const char* data,
                                    const char* content_type) {
    zhc_url_t parsed;
    if (zhc_url_parse(url, &parsed) != 0) {
        return NULL;
    }

    if (strcmp(parsed.protocol, "https") == 0) {
        return NULL;
    }

    int sock = zhc_tcp_connect(parsed.host, parsed.port);
    if (sock < 0) {
        return NULL;
    }

    size_t data_len = data ? strlen(data) : 0;

    /* 构造 HTTP 请求 */
    char request[8192];
    int req_len = snprintf(request, sizeof(request),
        "POST %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Connection: close\r\n"
        "User-Agent: ZHC-NET/1.0\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %zu\r\n"
        "\r\n",
        parsed.path, parsed.host,
        content_type ? content_type : "application/x-www-form-urlencoded",
        data_len);

    char* full_request = NULL;
    size_t full_len = (size_t)req_len + data_len + 1;
    full_request = malloc(full_len);
    if (!full_request) {
        zhc_tcp_close(sock);
        return NULL;
    }

    memcpy(full_request, request, (size_t)req_len);
    if (data && data_len > 0) {
        memcpy(full_request + req_len, data, data_len);
    }
    full_request[full_len - 1] = '\0';

    if (zhc_tcp_send(sock, full_request, full_len - 1) != (int)(full_len - 1)) {
        free(full_request);
        zhc_tcp_close(sock);
        return NULL;
    }
    free(full_request);

    /* 接收响应 */
    char* response = NULL;
    size_t response_capacity = 0;
    size_t response_len = 0;
    char recv_buf[4096];
    int n;

    zhc_tcp_set_timeout(sock, 10000);

    while ((n = zhc_tcp_recv(sock, recv_buf, sizeof(recv_buf) - 1)) > 0) {
        if (response_len + (size_t)n + 1 > response_capacity) {
            response_capacity = response_len + (size_t)n + 4096;
            response = realloc(response, response_capacity);
            if (!response) {
                zhc_tcp_close(sock);
                return NULL;
            }
        }
        memcpy(response + response_len, recv_buf, (size_t)n);
        response_len += (size_t)n;
    }
    zhc_tcp_close(sock);

    if (!response || response_len == 0) {
        free(response);
        return NULL;
    }
    response[response_len] = '\0';

    /* 解析 HTTP 响应（与 GET 相同） */
    zhc_http_response_t* resp = calloc(1, sizeof(zhc_http_response_t));
    if (!resp) {
        free(response);
        return NULL;
    }

    char* header_end = strstr(response, "\r\n\r\n");
    if (header_end) {
        *header_end = '\0';
        char* body = header_end + 4;

        char status_line[256];
        strncpy(status_line, response, sizeof(status_line) - 1);
        status_line[sizeof(status_line) - 1] = '\0';

        char* line = status_line;
        while (*line == ' ') line++;
        char* version_end = strchr(line, ' ');
        if (version_end) {
            char* status_start = version_end + 1;
            char* status_end = strchr(status_start, ' ');
            if (status_end) {
                *status_end = '\0';
            }
            resp->status_code = atoi(status_start);
        }

        resp->headers = strdup(response);

        char* cl = strstr(response, "Content-Length:");
        if (cl) {
            cl += 14;
            while (*cl == ' ' || *cl == '\t') cl++;
            char* cl_end = strchr(cl, '\r');
            if (cl_end) *cl_end = '\0';
            resp->content_length = atoi(cl);
        } else {
            resp->content_length = (int)strlen(body);
        }

        resp->content = strdup(body);

        char* ct = strstr(response, "Content-Type:");
        if (ct) {
            ct += 13;
            while (*ct == ' ' || *ct == '\t') ct++;
            char* ct_end = strchr(ct, '\r');
            if (ct_end) *ct_end = '\0';
            char* semi = strchr(ct, ';');
            if (semi) *semi = '\0';
            while (ct[strlen(ct) - 1] == ' ') ct[strlen(ct) - 1] = '\0';
            resp->content_type = strdup(ct);
        }
    } else {
        resp->status_code = 0;
        resp->content = strdup(response);
        resp->content_length = (int)strlen(response);
    }

    free(response);
    return resp;
}

void zhc_http_response_free(zhc_http_response_t* resp) {
    if (resp) {
        if (resp->status_text) free(resp->status_text);
        if (resp->headers) free(resp->headers);
        if (resp->content_type) free(resp->content_type);
        if (resp->content) free(resp->content);
        free(resp);
    }
}

/* ---------- DNS 实现 ---------- */

static char g_local_ip[64] = {0};
static char g_resolved_ip[256] = {0};

const char* zhc_get_local_ip(void) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        return NULL;
    }

    struct sockaddr_in google_dns;
    memset(&google_dns, 0, sizeof(google_dns));
    google_dns.sin_family = AF_INET;
    google_dns.sin_port = htons(53);
    inet_pton(AF_INET, "8.8.8.8", &google_dns.sin_addr);

    if (connect(sock, (struct sockaddr*)&google_dns, sizeof(google_dns)) == 0) {
        struct sockaddr_in local_addr;
        socklen_t addr_len = sizeof(local_addr);
        if (getsockname(sock, (struct sockaddr*)&local_addr, &addr_len) == 0) {
            inet_ntop(AF_INET, &local_addr.sin_addr, g_local_ip, sizeof(g_local_ip));
        }
    }

    close(sock);

    if (g_local_ip[0] == '\0') {
        strcpy(g_local_ip, "127.0.0.1");
    }

    return g_local_ip;
}

const char* zhc_resolve_host(const char* hostname) {
    struct hostent* he = gethostbyname(hostname);
    if (he == NULL) {
        return NULL;
    }

    if (he->h_addr_list[0] != NULL) {
        inet_ntop(he->h_addrtype, he->h_addr_list[0], g_resolved_ip, sizeof(g_resolved_ip));
        return g_resolved_ip;
    }

    return NULL;
}

#endif /* ZHC_NET_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_NET_H */
